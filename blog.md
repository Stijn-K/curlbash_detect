### **Do You Really Know What That Install Script Is Doing?**

You’ve probably seen this command a hundred times in install guides:

```bash
curl -sL example.com/install.sh | bash
```

It looks simple. It looks convenient. But do you **really** know what that script is doing?

When you run this command, you are blindly trusting that the script being served is safe, unaltered, and doing exactly what you expect. You have **no idea** what’s in that script before executing it—no chance to review the code, verify its integrity, or check for malicious commands.

Worse, did you know that the **server** can detect whether you are piping the script directly into `bash` or saving it to a file first? This means a malicious server (or an attacker who has compromised the server) could **serve different content depending on how the request is made.**

That’s right: if you simply `curl` the script into a file (`curl -O`), the response might be completely benign. But if you `curl | bash`, the server could recognize this and **serve a different script**—one that includes backdoors, data exfiltration commands, or worse.

In this blog, we’ll explore how this detection works, why it’s a serious security problem, and what you should do instead.

---

### **How a Server Can Detect** `curl | bash`

When you download a script using `curl`, the response comes in chunks and is either written to a file or executed immediately by `bash`. This distinction is something the **server can detect**.

One way to do this is by including a command that takes a while to complete in the script, such as:

```bash
sleep 2
```

If the script is being saved to a file, this delay has no effect on the TCP stream between the client and server. However, if it's being executed immediately, `bash` will pause for two seconds before continuing. The server can detect this delay and determine that the script is being executed in real time.

To make this detection more reliable, the server can exploit how data flows through buffers before reaching `bash`. Here’s how it works:

1. The server sends an initial script chunk containing the command `sleep 2`.
2. It then sends large amounts of junk data to fill up the TCP send and receive buffers, as well as `curl`'s internal buffer.
3. Once these buffers are full, `curl` and starts forwarding data to `bash`, and tells the server to temporarily stop sending data.
4. `bash` starts receiving data, which it executes line by line. When `bash` reaches `sleep 2`, it pauses execution for two seconds.
5. After 2 seconds, `bash` continues with the rest of the data it received, after which it hands control back to `curl`, which tells the server to continue sending data.
6. The server sees this two-second delay, which confirms that the script is being executed in real time.

If the server detects this delay, it **knows** that the script is being piped directly into `bash` and can modify the response accordingly.

---

### **In short**

1. You run `curl example.com/install.sh | bash`
2. The server detects that the script is being executed in real-time
3. It **changes the response on the fly**

This means:

- If you simply `curl` the script into a file (`curl -O`), the response might be benign.
- If you `curl | bash`, the server could serve **a completely different script**—including malicious payloads, backdoors, or data exfiltration commands.

---

### **Many Install Guides Encourage This Dangerous Practice**

The worst part? **Many official install guides tell you to do this.**

Several widely used tools recommend piping `curl` output directly to `bash`. Here are a few examples:

- **Rust** ([rust-lang.org](https://www.rust-lang.org/tools/install))
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  ```
- **Homebrew** ([brew.sh](https://brew.sh/))
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```
- **Node.js (Nodesource)** ([Nodesource setup guide](https://github.com/nodesource/distributions))
  ```bash
  curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  ```

Even well-intentioned maintainers may not realize how dangerous this is. But just because it's common **doesn’t make it safe**.

---

### **What should you do instead?**

Never pipe `curl` directly into `bash`. Instead, follow this **safer workflow**:

1. **Download the script first**
   ```bash
   curl -sL example.com/install.sh -o install.sh
   ```
2. **Inspect it**
   ```bash
   cat install.sh  # Or use `less` to read through it
   ```
3. **Verify its integrity** (if possible)
   ```bash
   sha256sum install.sh  # Compare with official checksum
   ```
4. **Run it manually**
   ```bash
   bash install.sh
   ```

This simple process ensures that the script hasn't been tampered with before execution.

---

### **Final Thoughts**

Piping `curl` output directly to `bash` is a security risk that too many people ignore. Worse, servers can detect this practice and **serve different scripts depending on how they’re executed**.

Instead of blindly running unverified scripts, always **download, inspect, and verify** before executing. A few extra seconds of caution could save you from a compromised system.

