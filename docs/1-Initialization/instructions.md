### Long term vision

StreamForStream is an application built to help new streamers help eachother grow through viewing each others streams, and giving feedback. Similar to how follow for follow is big on twitch, and raid trains, stream right is a more organic form of growth that involves individual interactions around streams. The idea is as following. You login to the application, and create an account. Here you link your twitch account, and other credentials. When you want to stream, you click on a go live button. At that point you'll get added to a list on the backend of live streamers. Viewers on the application can discover other viewers who are live on the app. We'll build some sort of discovery page. We'll track who you've viewed and for how long. There will be options to give feedback anonymously on the streamers you view. The idea is you'll earn some sort of credit score on the backend for viewing/giving feedback, and based off of how active you are you'll get more opportunities to attract other viewers


### Project layout

I want this to be a mono repo. I want to structure it similarly to C:\Users\toonm\workspace\gamenight

There is an infrastructure folder that we will add to later, that's where our cdk code will go in typescript. 

We have this docs folder which is where all our AI instructions/md documents will go.

We have a frontend, and backend folder that we'll fill out for now. 

I want the frontend to be a Next.JS app.

I want the backend to be a python FAST API application.

I want the client models to be generated from Open API.


### Initial project details

The long term vision is what we want to build to, but to get initial users I want to be as frictionless and feature light as possible.

You don't even need to login/create a user. Instead we can store the twitch profile in a search parameter or cookie, for the session. 

A user session should involve, going to a GetStarted page. Adding their twitch stream. From there they be brought to some sort of instructions page, where we give them instructions on how to use the app. The app will have a couple really basic features:

Start Viewing: User is brought to the view page, where they can start earning points for their twitch profile. 

Start Streaming: When a user wants to go live and use their points, they click go live and their twitch profile will be added to the list of streamers that are currently live.

### Landing PAge

We should immediately start promoting whoever is streaming now in the center of the landing page. I want the landing page to be really simple. 

1) It should show the logo
2)it should show who is streaming right now
3)It should show really simple directions on how to get started. 
- Add your stream
- Watch others stream, and engage in their chat. The more active you are, the more points you'll earn!
- When you're ready to go live, click go live! We'll promote your stream until you finish streaming for the day. 
4) There should be a button for Get Started

### Backend

The backend should be really simple. I want to follow the layout of how we structured folders in the backend for GameNight.

I think we'll just want a few API's to start, and in memory storage.


goLive(): Add your twitch stream to a list of streams that are currently live

reportView(): The frontend should report the view (streamerX watched StreamerY) every minute. We'll track view minutes in the back end. When we move to Dynamo, you can imagine we'd have a PK of ViewingStreamer, and a SK on timestamp viewed (ISO 8601, one minute granularity)

getLiveStreamers(): Used to render carousels of who is streaming. 

The backend should track who is currently live in memory when someone clicks goLive. Every five minutes or so, we should call the TwitchAPI to see if that user is still live. If not, log something and clear it from memory. If possible, we should also store how many viewers that person has, so we can use that to rank. Streamers with most viewers should be ranked first to start, to make the app seem more successful