I think we should change how the streams are ranked on the view page.

I want to rank lowest viewer/highest points first.

Can that ranking be applied on the backend? We also might need to be able to do some sort of pagination. I think we should paginate with a similar style to how we did it for GameNight in that folder, so we can  support DDB based indexes. 

I also want to make it so that we calculate two types of points. Point balance, and total points internally on the backend. We don't need to expose that on the UI, we should only show total points earned.

When someone views your stream for a minute, you should lose a point on your point balance. Lets use point balance for ranking, but show total points on the UI

Lets add in DDB functionality now to the backend, think of different ways to model this for me. 

I'm thinking there is one point balance table, that shows your total balance, and then separately there is the view_reporting table, that shows individual view records (one minute granularity, viewer x watched viewer y). Whenever a backend instance successfully writes a record for a minute, we should add a point to viewer x's balance, and subtract one from viewer y. 

When we do that we should update point balances by reading from DDB to get total point balance, and incrementing total point history and updating point balance.

Note someone can never earn more than one point a minute, so the important thing here is that PK is viewer channel and SK is eventminute on the views table