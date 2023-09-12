This one is much different than pytorch, because there's no way to pip install
a tensorflow that works with cuda 12.x right now (Sept 2023). 
Also, nvidia publishes an extremely good image from Google Brain for
the latest version of tensorflow that does support cuda 12.x.
So we instead build on that.