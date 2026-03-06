from __future__ import annotations

import logging
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable

from app.domain.streaming import (
    ENGAGEMENT_PRIORITY,
    VIEWER_COUNT_DESC,
    LiveStreamRecord,
    PaginatedLiveStreamResult,
    PointState,
    ResolvedChannel,
    SortMode,
    StreamState,
    ViewCreditResult,
    utc_now,
)

try:
    import boto3
    from boto3.dynamodb.conditions import Key
    from boto3.dynamodb.types import TypeSerializer
except ImportError:  # pragma: no cover - exercised only when boto3 is absent at runtime.
    boto3 = None
    Key = None
    TypeSerializer = None

try:
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover - exercised only when botocore is absent at runtime.
    ClientError = Exception

logger = logging.getLogger(__name__)

LIVE_PARTITION = "LIVE"
STREAMER_STATE_VIEWERS_INDEX = "live_viewers"
STREAMER_STATE_ENGAGEMENT_INDEX = "live_engagement"
SORT_INT_WIDTH = 20
SORT_INT_MAX = (10**SORT_INT_WIDTH) - 1
MAX_WRITE_RETRIES = 4


def _normalize_channel_login(channel_login: str) -> str:
    return channel_login.strip().lower()


def _as_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, bool):
        return int(value)
    return int(value)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _parse_datetime(raw: Any, *, fallback: datetime | None = None) -> datetime:
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str) and raw:
        return datetime.fromisoformat(raw)
    if fallback is not None:
        return fallback
    return utc_now()


def _sortable_int(value: int, *, descending: bool) -> str:
    safe_value = max(0, min(value, SORT_INT_MAX))
    comparable = SORT_INT_MAX - safe_value if descending else safe_value
    return f"{comparable:0{SORT_INT_WIDTH}d}"


def _viewer_sort_key(viewer_count: int, went_live_at: datetime, channel_login: str) -> str:
    return f"VC#{_sortable_int(viewer_count, descending=True)}#WL#{_serialize_datetime(went_live_at)}#CL#{channel_login}"


def _engagement_sort_key(viewer_count: int, point_balance: int, went_live_at: datetime, channel_login: str) -> str:
    return (
        f"VC#{_sortable_int(viewer_count, descending=False)}"
        f"#PB#{_sortable_int(point_balance, descending=True)}"
        f"#WL#{_serialize_datetime(went_live_at)}"
        f"#CL#{channel_login}"
    )


class DynamoDBStreamingStore:
    def __init__(
        self,
        *,
        region_name: str,
        endpoint_url: str | None,
        streamer_state_table_name: str,
        view_reports_table_name: str,
    ) -> None:
        if boto3 is None or Key is None or TypeSerializer is None:
            raise RuntimeError("boto3 is required when STREAMING_STORE_BACKEND=dynamodb.")
        if not streamer_state_table_name or not view_reports_table_name:
            raise RuntimeError(
                "DDB_STREAMER_STATE_TABLE_NAME and DDB_VIEW_REPORTS_TABLE_NAME are required when "
                "STREAMING_STORE_BACKEND=dynamodb."
            )

        dynamodb = boto3.resource("dynamodb", region_name=region_name, endpoint_url=endpoint_url)
        self._streamer_state_table = dynamodb.Table(streamer_state_table_name)
        self._view_reports_table = dynamodb.Table(view_reports_table_name)
        self._streamer_state_table_name = streamer_state_table_name
        self._view_reports_table_name = view_reports_table_name
        self._client = dynamodb.meta.client
        self._serializer = TypeSerializer()

    def _serialize_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: self._serializer.serialize(value) for key, value in item.items()}

    def _serialize_values(self, values: dict[str, Any]) -> dict[str, Any]:
        return {key: self._serializer.serialize(value) for key, value in values.items()}

    def _is_conditional_failure(self, exc: Exception) -> bool:
        if not isinstance(exc, ClientError):
            return False
        code = exc.response.get("Error", {}).get("Code")
        return code in {"ConditionalCheckFailedException", "TransactionCanceledException", "TransactionConflictException"}

    def _next_version(self, current: dict[str, Any] | None) -> int:
        return _as_int(current.get("version", 0)) + 1 if current else 1

    def _refresh_live_indexes(self, item: dict[str, Any]) -> dict[str, Any]:
        if item.get("is_live"):
            viewer_count = max(0, _as_int(item.get("viewer_count", 0)))
            point_balance = max(0, _as_int(item.get("point_balance", 0)))
            went_live_at = _parse_datetime(item.get("went_live_at"))
            channel_login = _normalize_channel_login(_as_str(item.get("channel_login")))

            item["is_live"] = True
            item["viewer_count"] = viewer_count
            item["point_balance"] = point_balance
            item["went_live_at"] = _serialize_datetime(went_live_at)
            item["live_viewers_pk"] = LIVE_PARTITION
            item["live_viewers_sk"] = _viewer_sort_key(viewer_count, went_live_at, channel_login)
            item["live_engagement_pk"] = LIVE_PARTITION
            item["live_engagement_sk"] = _engagement_sort_key(viewer_count, point_balance, went_live_at, channel_login)
            return item

        item["is_live"] = False
        for field in (
            "viewer_count",
            "stream_title",
            "game_name",
            "went_live_at",
            "live_viewers_pk",
            "live_viewers_sk",
            "live_engagement_pk",
            "live_engagement_sk",
        ):
            item.pop(field, None)
        return item

    def _get_streamer_item(self, channel_login: str, *, consistent: bool) -> dict[str, Any] | None:
        response = self._streamer_state_table.get_item(
            Key={"channel_login": _normalize_channel_login(channel_login)},
            ConsistentRead=consistent,
        )
        return response.get("Item")

    def _view_report_exists(self, viewer_channel_login: str, viewed_minute: str) -> bool:
        response = self._view_reports_table.get_item(
            Key={
                "viewer_channel_login": _normalize_channel_login(viewer_channel_login),
                "viewed_minute": viewed_minute,
            },
            ConsistentRead=True,
        )
        return "Item" in response

    def _put_streamer_item(
        self,
        channel_login: str,
        mutate: Callable[[dict[str, Any] | None], dict[str, Any] | None],
    ) -> dict[str, Any] | None:
        login = _normalize_channel_login(channel_login)
        for attempt in range(MAX_WRITE_RETRIES):
            current = self._get_streamer_item(login, consistent=True)
            next_item = mutate(deepcopy(current) if current else None)
            if next_item is None:
                return None

            next_item["channel_login"] = login
            next_item["point_balance"] = max(0, _as_int(next_item.get("point_balance", 0)))
            next_item["total_points"] = max(0, _as_int(next_item.get("total_points", 0)))
            next_item["version"] = self._next_version(current)
            self._refresh_live_indexes(next_item)

            try:
                if current is None:
                    self._streamer_state_table.put_item(
                        Item=next_item,
                        ConditionExpression="attribute_not_exists(channel_login)",
                    )
                else:
                    self._streamer_state_table.put_item(
                        Item=next_item,
                        ConditionExpression="attribute_not_exists(#version) OR #version = :expected_version",
                        ExpressionAttributeNames={"#version": "version"},
                        ExpressionAttributeValues={":expected_version": _as_int(current.get("version", 0))},
                    )
                return next_item
            except ClientError as exc:
                if self._is_conditional_failure(exc) and attempt < MAX_WRITE_RETRIES - 1:
                    continue
                raise

        raise RuntimeError(f"Failed to write streamer state for {login} after retries.")

    def _item_to_point_state(self, item: dict[str, Any] | None) -> PointState:
        if item is None:
            return PointState(point_balance=0, total_points=0)
        return PointState(
            point_balance=max(0, _as_int(item.get("point_balance", 0))),
            total_points=max(0, _as_int(item.get("total_points", 0))),
        )

    def _item_to_profile(self, item: dict[str, Any] | None) -> ResolvedChannel | None:
        if item is None:
            return None
        display_name = _as_str(item.get("channel_display_name"))
        channel_url = _as_str(item.get("channel_url"))
        if not display_name or not channel_url:
            return None
        return ResolvedChannel(
            channel_login=_normalize_channel_login(_as_str(item.get("channel_login"))),
            channel_display_name=display_name,
            profile_image_url=_as_str(item.get("profile_image_url")),
            channel_url=channel_url,
        )

    def _item_to_live_record(self, item: dict[str, Any] | None) -> LiveStreamRecord | None:
        if item is None or not item.get("is_live"):
            return None
        channel_login = _normalize_channel_login(_as_str(item.get("channel_login")))
        went_live_at = _parse_datetime(item.get("went_live_at"), fallback=utc_now())
        updated_at = _parse_datetime(item.get("updated_at"), fallback=went_live_at)
        return LiveStreamRecord(
            channel_login=channel_login,
            channel_display_name=_as_str(item.get("channel_display_name")) or channel_login,
            profile_image_url=_as_str(item.get("profile_image_url")),
            channel_url=_as_str(item.get("channel_url")) or f"https://www.twitch.tv/{channel_login}",
            stream_title=_as_str(item.get("stream_title")),
            game_name=_as_str(item.get("game_name")),
            viewer_count=max(0, _as_int(item.get("viewer_count", 0))),
            is_live=True,
            went_live_at=went_live_at,
            updated_at=updated_at,
            point_balance=max(0, _as_int(item.get("point_balance", 0))),
            total_points=max(0, _as_int(item.get("total_points", 0))),
        )

    def _key_token_from_item(self, item: dict[str, Any], sort_mode: SortMode) -> dict[str, str]:
        if sort_mode == VIEWER_COUNT_DESC:
            return {
                "channel_login": _as_str(item["channel_login"]),
                "live_viewers_pk": _as_str(item["live_viewers_pk"]),
                "live_viewers_sk": _as_str(item["live_viewers_sk"]),
            }
        return {
            "channel_login": _as_str(item["channel_login"]),
            "live_engagement_pk": _as_str(item["live_engagement_pk"]),
            "live_engagement_sk": _as_str(item["live_engagement_sk"]),
        }

    def _validate_cursor(self, cursor: dict[str, str] | None, sort_mode: SortMode) -> dict[str, str] | None:
        if cursor is None:
            return None
        required_keys = (
            {"channel_login", "live_viewers_pk", "live_viewers_sk"}
            if sort_mode == VIEWER_COUNT_DESC
            else {"channel_login", "live_engagement_pk", "live_engagement_sk"}
        )
        if set(cursor.keys()) != required_keys:
            raise ValueError("Invalid cursor payload")
        return cursor

    def _build_transact_put(self, item: dict[str, Any], current: dict[str, Any] | None) -> dict[str, Any]:
        request: dict[str, Any] = {
            "TableName": self._streamer_state_table_name,
            "Item": self._serialize_item(item),
        }
        if current is None:
            request["ConditionExpression"] = "attribute_not_exists(#channel_login)"
            request["ExpressionAttributeNames"] = {"#channel_login": "channel_login"}
        else:
            request["ConditionExpression"] = "attribute_not_exists(#version) OR #version = :expected_version"
            request["ExpressionAttributeNames"] = {"#version": "version"}
            request["ExpressionAttributeValues"] = self._serialize_values(
                {":expected_version": _as_int(current.get("version", 0))}
            )
        return request

    def upsert_profile(self, channel: ResolvedChannel) -> ResolvedChannel:
        def mutate(current: dict[str, Any] | None) -> dict[str, Any]:
            item = dict(current or {})
            item.update(
                {
                    "channel_login": _normalize_channel_login(channel.channel_login),
                    "channel_display_name": channel.channel_display_name,
                    "profile_image_url": channel.profile_image_url,
                    "channel_url": channel.channel_url,
                    "updated_at": _serialize_datetime(utc_now()),
                }
            )
            return item

        self._put_streamer_item(channel.channel_login, mutate)
        return ResolvedChannel(
            channel_login=_normalize_channel_login(channel.channel_login),
            channel_display_name=channel.channel_display_name,
            profile_image_url=channel.profile_image_url,
            channel_url=channel.channel_url,
        )

    def get_profile(self, channel_login: str) -> ResolvedChannel | None:
        return self._item_to_profile(self._get_streamer_item(channel_login, consistent=True))

    def get_point_state(self, channel_login: str) -> PointState:
        return self._item_to_point_state(self._get_streamer_item(channel_login, consistent=True))

    def upsert_live_stream(self, profile: ResolvedChannel, stream_state: StreamState) -> LiveStreamRecord:
        now = utc_now()

        def mutate(current: dict[str, Any] | None) -> dict[str, Any]:
            current_record = self._item_to_live_record(current)
            item = dict(current or {})
            item.update(
                {
                    "channel_login": _normalize_channel_login(profile.channel_login),
                    "channel_display_name": profile.channel_display_name,
                    "profile_image_url": profile.profile_image_url,
                    "channel_url": profile.channel_url,
                    "stream_title": stream_state.stream_title,
                    "game_name": stream_state.game_name,
                    "viewer_count": max(0, stream_state.viewer_count),
                    "is_live": True,
                    "went_live_at": _serialize_datetime(current_record.went_live_at if current_record else now),
                    "updated_at": _serialize_datetime(now),
                }
            )
            return item

        item = self._put_streamer_item(profile.channel_login, mutate)
        record = self._item_to_live_record(item)
        if record is None:
            raise RuntimeError("Failed to create live stream record.")
        return record

    def get_live_stream(self, channel_login: str) -> LiveStreamRecord | None:
        return self._item_to_live_record(self._get_streamer_item(channel_login, consistent=True))

    def remove_live_stream(self, channel_login: str) -> bool:
        removed = False

        def mutate(current: dict[str, Any] | None) -> dict[str, Any] | None:
            nonlocal removed
            if current is None or not current.get("is_live"):
                return None
            removed = True
            item = dict(current)
            item["is_live"] = False
            item["updated_at"] = _serialize_datetime(utc_now())
            return item

        self._put_streamer_item(channel_login, mutate)
        return removed

    def list_live_streams(
        self,
        *,
        exclude_channel_login: str | None = None,
        limit: int = 20,
        cursor: dict[str, str] | None = None,
        sort_mode: SortMode,
    ) -> PaginatedLiveStreamResult:
        if sort_mode == VIEWER_COUNT_DESC:
            index_name = STREAMER_STATE_VIEWERS_INDEX
            partition_key = "live_viewers_pk"
        elif sort_mode == ENGAGEMENT_PRIORITY:
            index_name = STREAMER_STATE_ENGAGEMENT_INDEX
            partition_key = "live_engagement_pk"
        else:
            raise ValueError("Unsupported sort mode")

        exclude = _normalize_channel_login(exclude_channel_login) if exclude_channel_login else None
        items: list[LiveStreamRecord] = []
        next_key = self._validate_cursor(cursor, sort_mode)

        while len(items) < limit:
            fetch_limit = max(limit - len(items), 1)
            if exclude:
                fetch_limit = min(max(fetch_limit * 2, fetch_limit), 100)

            query_kwargs: dict[str, Any] = {
                "IndexName": index_name,
                "KeyConditionExpression": Key(partition_key).eq(LIVE_PARTITION),
                "Limit": fetch_limit,
                "ScanIndexForward": True,
            }
            if next_key:
                query_kwargs["ExclusiveStartKey"] = next_key

            response = self._streamer_state_table.query(**query_kwargs)
            page_items = response.get("Items", [])
            last_consumed_item: dict[str, Any] | None = None
            last_consumed_index = -1

            for index, item in enumerate(page_items):
                record = self._item_to_live_record(item)
                if record is None:
                    continue
                if exclude and record.channel_login == exclude:
                    continue
                items.append(record)
                last_consumed_item = item
                last_consumed_index = index
                if len(items) >= limit:
                    break

            last_evaluated_key = response.get("LastEvaluatedKey")
            if len(items) >= limit:
                has_unconsumed_items = last_consumed_index + 1 < len(page_items)
                if last_consumed_item and (has_unconsumed_items or last_evaluated_key is not None):
                    return PaginatedLiveStreamResult(
                        items=items,
                        next_cursor=self._key_token_from_item(last_consumed_item, sort_mode),
                    )
                return PaginatedLiveStreamResult(items=items, next_cursor=None)

            if not last_evaluated_key:
                break
            next_key = last_evaluated_key

        return PaginatedLiveStreamResult(items=items, next_cursor=None)

    def all_live_logins(self) -> list[str]:
        items: list[str] = []
        next_key: dict[str, Any] | None = None

        while True:
            query_kwargs: dict[str, Any] = {
                "IndexName": STREAMER_STATE_VIEWERS_INDEX,
                "KeyConditionExpression": Key("live_viewers_pk").eq(LIVE_PARTITION),
                "ProjectionExpression": "channel_login",
                "ScanIndexForward": True,
            }
            if next_key:
                query_kwargs["ExclusiveStartKey"] = next_key

            response = self._streamer_state_table.query(**query_kwargs)
            items.extend(_normalize_channel_login(_as_str(item.get("channel_login"))) for item in response.get("Items", []))
            next_key = response.get("LastEvaluatedKey")
            if not next_key:
                return items

    def refresh_live_stream(self, channel_login: str, stream_state: StreamState) -> LiveStreamRecord | None:
        now = utc_now()

        def mutate(current: dict[str, Any] | None) -> dict[str, Any] | None:
            if current is None or not current.get("is_live"):
                return None
            item = dict(current)
            item.update(
                {
                    "stream_title": stream_state.stream_title,
                    "game_name": stream_state.game_name,
                    "viewer_count": max(0, stream_state.viewer_count),
                    "is_live": bool(stream_state.is_live),
                    "updated_at": _serialize_datetime(now),
                }
            )
            return item

        item = self._put_streamer_item(channel_login, mutate)
        return self._item_to_live_record(item)

    def apply_view_report(
        self,
        *,
        viewer_channel_login: str,
        target_channel_login: str,
        viewed_minute: str,
    ) -> ViewCreditResult:
        viewer_login = _normalize_channel_login(viewer_channel_login)
        target_login = _normalize_channel_login(target_channel_login)
        if viewer_login == target_login:
            raise ValueError("A streamer cannot earn points by viewing their own channel.")

        for attempt in range(MAX_WRITE_RETRIES):
            if self._view_report_exists(viewer_login, viewed_minute):
                viewer_state = self.get_point_state(viewer_login)
                return ViewCreditResult(
                    credited=False,
                    viewer_points_balance=viewer_state.point_balance,
                    viewer_total_points=viewer_state.total_points,
                )

            viewer_item = self._get_streamer_item(viewer_login, consistent=True)
            target_item = self._get_streamer_item(target_login, consistent=True)
            viewer_state = self._item_to_point_state(viewer_item)
            target_state = self._item_to_point_state(target_item)
            now = utc_now()

            viewer_next = dict(viewer_item or {"channel_login": viewer_login})
            viewer_next.update(
                {
                    "channel_login": viewer_login,
                    "point_balance": viewer_state.point_balance + 1,
                    "total_points": viewer_state.total_points + 1,
                    "updated_at": _serialize_datetime(now),
                    "version": self._next_version(viewer_item),
                }
            )
            self._refresh_live_indexes(viewer_next)

            target_next = dict(target_item or {"channel_login": target_login})
            target_next.update(
                {
                    "channel_login": target_login,
                    "point_balance": max(0, target_state.point_balance - 1),
                    "total_points": target_state.total_points,
                    "updated_at": _serialize_datetime(now),
                    "version": self._next_version(target_item),
                }
            )
            self._refresh_live_indexes(target_next)

            try:
                self._client.transact_write_items(
                    TransactItems=[
                        {
                            "Put": {
                                "TableName": self._view_reports_table_name,
                                "Item": self._serialize_item(
                                    {
                                        "viewer_channel_login": viewer_login,
                                        "viewed_minute": viewed_minute,
                                        "target_channel_login": target_login,
                                        "credited_at": _serialize_datetime(now),
                                    }
                                ),
                                "ConditionExpression": "attribute_not_exists(#viewer_channel_login) AND "
                                "attribute_not_exists(#viewed_minute)",
                                "ExpressionAttributeNames": {
                                    "#viewer_channel_login": "viewer_channel_login",
                                    "#viewed_minute": "viewed_minute",
                                },
                            }
                        },
                        {"Put": self._build_transact_put(viewer_next, viewer_item)},
                        {"Put": self._build_transact_put(target_next, target_item)},
                    ]
                )
                return ViewCreditResult(
                    credited=True,
                    viewer_points_balance=viewer_state.point_balance + 1,
                    viewer_total_points=viewer_state.total_points + 1,
                )
            except ClientError as exc:
                if self._view_report_exists(viewer_login, viewed_minute):
                    current_viewer_state = self.get_point_state(viewer_login)
                    return ViewCreditResult(
                        credited=False,
                        viewer_points_balance=current_viewer_state.point_balance,
                        viewer_total_points=current_viewer_state.total_points,
                    )
                if self._is_conditional_failure(exc) and attempt < MAX_WRITE_RETRIES - 1:
                    logger.info("Retrying view report transaction after DynamoDB contention for %s", viewer_login)
                    continue
                raise

        raise RuntimeError(f"Failed to apply view report for {viewer_login} after retries.")


def create_dynamodb_storage(
    *,
    region_name: str,
    endpoint_url: str | None,
    streamer_state_table_name: str,
    view_reports_table_name: str,
) -> DynamoDBStreamingStore:
    return DynamoDBStreamingStore(
        region_name=region_name,
        endpoint_url=endpoint_url,
        streamer_state_table_name=streamer_state_table_name,
        view_reports_table_name=view_reports_table_name,
    )
