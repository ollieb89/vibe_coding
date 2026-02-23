---
title: Security Hardening Instructions
source: instructions/security-hardening.instructions.md
---

### Content
---
description: 'Security hardening best practices for web applications - OWASP, injection prevention, authentication, encryption'
applyTo: '**/*.py, **/*.js, **/*.ts, **/*.java, **/*.go, **/*.rb'
subjects: [security, owasp, vulnerability, injection, xss, authentication, encryption, hardening]
category: security
---

# Security Hardening Instructions

Apply these security best practices to all application code.

## 1. Injection Prevention

### SQL Injection

```python
# ❌ BAD: String concatenation (SQLi vulnerable)
query = f"SELECT * FROM users WHERE email = '{email}'"
cursor.execute(query)

# ✅ GOOD: Parameterized queries
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# ✅ GOOD: ORM with proper filtering
User.objects.filter(email=email).first()
```

```javascript
// ❌ BAD: Template literals in SQL
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ GOOD: Parameterized query
const query = 'SELECT * FROM users WHERE id = $1';
await pool.query(query, [userId]);
```

### Command Injection

```python
# ❌ BAD: Shell injection vulnerable
os.system(f"ping {user_input}")
subprocess.call(f"convert {filename}", shell=True)

# ✅ GOOD: Avoid shell, use list arguments
subprocess.run(["ping", "-c", "4", validated_host], shell=False)

# ✅ GOOD: Whitelist allowed values
ALLOWED_HOSTS = {"google.com", "github.com"}
if host in ALLOWED_HOSTS:
    subprocess.run(["ping", "-c", "4", host])
```

### NoSQL Injection

```javascript
// ❌ BAD: Operator injection in MongoDB
db.users.find({ username: req.body.username });

// ✅ GOOD: Use a library with proper escaping or parameterized queries
const mongoose = require('mongoose');
const UserSchema = new mongoose.Schema({ ... });
const User = mongoose.model('User', UserSchema);
const user = await User.findOne({ username: req.body.username }).exec();
```

[source: instructions/security-hardening.instructions.md]