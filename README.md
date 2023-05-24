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

# Detecting curl | bash
## How it works
We know that bash executes everything line by line, this means that if we include a command like `sleep 2`, the execution will pause for 2 seconds.
This means that if we include this `sleep 2` at the start of our TCP stream, the TCP send stream will pause while the sleep executes. This pause can be detected by the server.
Unfortunately, simply sending a `sleep 2` will not work as there are multiple buffers between what the server sends, and what bash executes, that we will need to fill before bash actually executes anything.

The flow of data between the server and bash looks like this:
1. Server
2. Send buffer (dynamically adjusted)

3. Recv buffer (dynamically adjusted)
4. curl (CURL\_MAX\_WRITE\_SIZE)
5. bash (line by line)

We thus need to fill 3 buffers before bash will see our response...
The first two buffers, the send and recv buffer, are "auto tuned", this means that their size may vary depending on the current requirements.
We can control the send buffer, but we can't control the recv buffer.

To control the send buffer we can use the following line:
```
client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 87380)
```
We use 87380 here because it already is the default size for ubuntu.
By fixing the send buffer we remove one uncertainty, making the detection easier and more reliable.

The recv buffer is something that we can't control, but experimenting shows that on kali-linux, about 2MB is needed to fill up the buffer.
This amount of data also already seems enough to overflow the curl buffer.

## So what happens?
- The client makes a request to the server.
- The server responds with a chunked HTTP response, where the first chunk contains the `sleep 2` command, and 64 chunks follow, each containing 87380 null-bytes.
- The client's buffers should now be filling up, and curl should start forwarding the response to either stdout or bash.
- If the response is redirected to stdout, nothing is done with the sleep command and the TCP connection will only pause for a short while.
- If the response is instead redirected to bash, the sleep command will be executed first, after which curl is able to empty the rest of its buffer. This means that the TCP connection will pause for 2 seconds.
- The server measures the delays between each chunk it sends, if the delay gets close, or over, 2 seconds, it is likely that the `sleep 2` command was executed, and `curl <url> | bash` is used.
- If between all 64 chunks no significant delay was detected, it is likely that just `curl <url>` was used.
 

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
- https://www.idontplaydarts.com/2016/04/detecting-curl-pipe-bash-server-side/ (unreachable as of 24/05/2023)
	- https://web.archive.org/web/20230408195648/https://www.idontplaydarts.com/2016/04/detecting-curl-pipe-bash-server-side/
- a unknown reddit user claiming this is possible and linking the above blogpost.
