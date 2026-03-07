I have this idea for what I want to do next for the app, but I need help fleshing it out.

Right now we only add points, when we create a view event for a channel.

The problem we're going to run into, is really streamers are a small market and you'll
never get more than a small number of viewers through this app.

I think what we want is a mechanism to attract viewers, to view on your behalf.

Right now there isn't auth or anything, users can just pick a channel that they want
to promote.  

I think this is great, because any user can technically view for another channel.

But we have dedup mechanisms, where we report views with a PK on the view table of viewer channlel.

I'm trying to think how can we scale this out long term?

A couple options -

- we use IP addresses, you view on the behalf of another channel.

-We just continue with deduping

- long term we add in user log ins, with logins you can save the points to your login and gift those points to your favorite streamer/use those points to boost a streamer.
You get points by watching your streamer, and use those points to boost that same streamer? that seems complex... Perhaps we want the points to always go to a channel and not get cached on the user login. 