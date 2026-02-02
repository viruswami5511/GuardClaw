\# 🔒 GuardClaw Scanner



\*\*Security scanner for OpenClaw configurations\*\*  

Find risky deployment patterns before they become incidents.



\[MIT License] · Python 3.8+



---



\## What is GuardClaw Scanner?



\*\*GuardClaw Scanner\*\* is a local, open-source tool that scans

\[OpenClaw](https://openclaw.com) configuration files for common

\*\*real-world deployment risks\*\*, such as:



\- plaintext API keys

\- exposed admin endpoints

\- unsafe debug or execution settings



This tool \*\*does not judge OpenClaw\*\*.

OpenClaw is a powerful framework.



GuardClaw Scanner focuses on \*\*how OpenClaw is configured and deployed in practice\*\*.



---



\## Why this exists



OpenClaw is often:

\- self-hosted

\- customized

\- deployed quickly



In real deployments, this can lead to:

\- API keys committed to git

\- services bound to `0.0.0.0`

\- debug logging leaking secrets



These are \*\*deployment risks\*\*, not framework flaws.



GuardClaw Scanner makes these risks visible.



---



\## What GuardClaw Scanner checks



\- 🚨 \*\*Plaintext secrets\*\*

&nbsp; - API keys for Anthropic, OpenAI, GitHub, Stripe, AWS, etc.

\- ⚠️ \*\*Exposed endpoints\*\*

&nbsp; - Services bound to all network interfaces

\- ℹ️ \*\*Unsafe configuration flags\*\*

&nbsp; - Debug mode, permissive execution settings

\- ℹ️ \*\*Logging risks\*\*

&nbsp; - Log files that may contain secrets

\- ℹ️ \*\*File permissions\*\*

&nbsp; - Unix-only checks for world-readable config files



Each finding includes:

\- severity (Critical / High / Medium / Low)

\- \*\*context explaining when it matters\*\*

\- concrete remediation steps



---



\## What this tool does NOT do



\- ❌ It does not scan OpenClaw source code

\- ❌ It does not claim OpenClaw is insecure

\- ❌ It does not send your data anywhere

\- ❌ It does not replace proper secrets management



Everything runs \*\*locally\*\*.  

You can verify this by reading the code.



---



\## Quick start



```bash

git clone https://github.com/yourusername/guardclaw.git

cd guardclaw

pip install -r requirements.txt

