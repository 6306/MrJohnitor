<h1>Mr. Johnitor</h1>
<h3>A chatbot for Discord that learns how to speak by listening to people.</h3>

<br><br>

<h1>Overview</h1>
<p>
Mr. Johnitor is a Markov-chain based Discord chatbot. It passively listens to messages in servers,
learns from them, and generates responses when mentioned or replied to.
</p>

<p>
The bot also includes owner-only moderation tools to prevent certain users from being mentioned
or referenced in generated messages.
</p>

<br>

<h1>Requirements</h1>
<p>Python 3.8+ (Original server ran on Windows 7 Home Professional SP1</p>
<p>discord.py version 2.3.2 or greater</p>
<p>markovify version 0.9.4 or greater</p>

<br><br>

<h1>Installation</h1>
<pre>
pip install -r requirements.txt
</pre>

<p>
Set your Discord bot token and your personal Discord user ID inside the script before running.
</p>

<br>

<h1>Commands</h1>

<h2>Owner-Only Commands</h2>
<p>These commands can only be used by the bot owner (OWNER_ID).</p>

<h3><code>!add @user</code> or <code>!add &lt;user_id&gt;</code></h3>
<p>
Adds a user to the ban list.  
Banned users will:
</p>
<ul>
  <li>Never be mentioned by the bot</li>
  <li>Have their mentions replaced with <b>Non-mentionable User</b> in all bot messages</li>
</ul>
<p>
Banned users are stored persistently in <code>banned_users.json</code>.
</p>

<br>

<h3><code>!remove @user</code> or <code>!remove &lt;user_id&gt;</code></h3>
<p>
Removes a user from the ban list and restores normal mention behavior.
</p>

<br>

<h3><code>!listbanned</code></h3>
<p>
Displays a list of all currently banned users.
</p>

<br>

<h3><code>!clearbans</code></h3>
<p>
Clears the entire ban list and resets <code>banned_users.json</code>.
</p>

<br>

<h2>Information & Utility Commands</h2>

<h3><code>!chaininfo</code></h3>
<p>
Shows basic information about the bot’s learning state:
</p>
<ul>
  <li>Total collected messages</li>
  <li>Whether a Markov model is saved to disk</li>
</ul>

<br>

<h3><code>!unique</code></h3>
<p>
Displays how many unique messages the bot has learned compared to total messages.
</p>

<br>

<h3><code>!save</code></h3>
<p>
Forces a rebuild of the Markov model and saves it to <code>model.json</code>.
Also shows how long the rebuild took.
</p>

<br>

<h2>Chat Behavior (No Command Required)</h2>

<h3>Mentions & Replies</h3>
<p>
If you mention Mr. Johnitor or reply to one of its messages, it will generate a Markov-based reply.
</p>

<br>

<h3>Passive Learning</h3>
<p>
The bot automatically learns from <b>all messages</b> in channels it can read,
including its own messages.
</p>

<br>

<h3>Background Self-Talk</h3>
<p>
Every 15–90 minutes, the bot may randomly begin talking to itself in the last active channel
for up to 30 seconds.
</p>

<br>

<h3>Self-Mention Loop</h3>
<p>
If the bot mentions itself, it will enter a 30-second “insanity loop” where it talks to itself
at random intervals.
</p>

<br>

<h1>Files Generated</h1>

<ul>
  <li><code>messages.txt</code> – Raw collected messages</li>
  <li><code>model.json</code> – Serialized Markov model</li>
  <li><code>banned_users.json</code> – List of banned users as Discord mentions</li>
</ul>

<br>

<h1>Notes</h1>
<ul>
  <li>Banned words are filtered before messages are sent</li>
  <li>The bot avoids repeating its last response</li>
  <li>All file writes are thread-safe</li>
  <li>No external databases required</li>
</ul>

<br><br>

<h1>License</h1>

<p>
<b>This project is licensed under the <b>GNU GENERAL PUBLIC LICENSE (GPL)</b>.
</p>

<p>
You are free to:
</p>
<ul>
  <li>Use the software</li>
  <li>Modify the software</li>
  <li>Distribute the software</li>
</ul>

<p>
Under the condition that any distributed modifications are also licensed
under the GPL.
</p>
