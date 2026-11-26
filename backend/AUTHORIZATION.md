# Authorization policy

All newly registered accounts receive the `user` role. Users may read and change their own profile, collections,
ratings, reviews, passport stamps and activity; requests naming another user's ID receive `403 Forbidden`.
Catalog reads and public profile listing remain public. Catalog create/update/delete and `/admin/*` operations require
an `admin` account. Tokens are short-lived JWT Bearer tokens; configure `JWT_SECRET_KEY` with a random secret of at
least 32 bytes before starting the API.

Promote an account to administrator through a trusted database administration channel (never through the public API):

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
```
