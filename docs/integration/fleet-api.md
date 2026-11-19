# Fleet API (VMMS serves, BMS reads)

VMMS owns the trucks and garages. BMS reads them from VMMS through three read only routes instead of the old Capstone 1 database (`welinc_db`).

## Who calls it

Only BMS dispatch, as client `bms` with a service token. No person ever calls these routes, and they answer no person data.

1. BMS dispatch asks welinc-auth for a token: `POST /auth/token` with `grant_type=client_credentials`, `audience=VMMS`, `scope=fleet.read` and its client assertion. The answer is a token with `aud: VMMS`, `token_use: service` and `scope: fleet.read`.
2. It calls VMMS on the internal network (`VMMS_INTERNAL_URL`, `http://vmms-backend:3010` locally), not through the public gateway.

The copied `src/auth/verify/service-token-client.ts` does step 1 for you: it keeps the token until 60 s before its `exp` and shares one request between callers. Ask it for audience `VMMS` and scope `fleet.read`.

## Routes

| Route | Method | Answer |
|---|---|---|
| `/vmms/fleet/vehicles` | GET | `{ vehicles: FleetVehicle[] }`: every vehicle with `isActive` true and `deletedAt` null, ordered by `plateNumber`. `?garageId=<uuid>` keeps one garage's |
| `/vmms/fleet/vehicles/:id` | GET | one `FleetVehicle`; a soft deleted or unknown id answers 404 `VEHICLE_NOT_FOUND` |
| `/vmms/fleet/garages` | GET | `{ garages: { id, name }[] }`: active and not deleted, ordered by `name` |

```ts
type FleetVehicle = {
  id: string;            // uuid, VMMS vehicles.id
  plateNumber: string;
  make: string | null;
  model: string;
  year: number | null;
  truckSizeCategory: string | null;
  capacity: number;
  odometer: number;
  status: 'AVAILABLE' | 'UNDER_REPAIR' | 'UNDER_MAINTENANCE'; // VMMS VehicleStatus
  garageId: string | null;
  updatedAt: string;     // ISO 8601
};
```

Each field is the VMMS `vehicles` column of the same name. `engineType` is not served. Every answer carries `Cache-Control: no-store`: the caller owns its cache.

## Auth answers

| Request | Answer |
|---|---|
| No token, or a bad one | 401 |
| An expired token | 401 `TOKEN_EXPIRED`: get a new token and retry once |
| A person's token (any system) | 403 `WRONG_TOKEN_USE` |
| A service token without `fleet.read` | 403 `FORBIDDEN` |
| A service token with `aud` other than `VMMS` | 401 `WRONG_AUDIENCE` |

**VMMS side:** put `@ServiceRoute('fleet.read')` from the copied `src/auth/verify/guards.ts` on the controller. It refuses a person's token (`WRONG_TOKEN_USE`) and a missing scope (`FORBIDDEN`), and your user guard skips routes marked with it. The checker can't make a service token without the scope (that needs a client key), so prove the 403 `FORBIDDEN` with a VMMS unit test using `src/auth/verify/testing/test-auth.ts`.

## BMS rules

| Rule | Why |
|---|---|
| The vehicle list is cached 30 s and shows every active vehicle with its VMMS status | Dispatchers see what VMMS sees, a few seconds late at most |
| At assignment, read the one vehicle fresh (`GET /vmms/fleet/vehicles/:id`, never the cache) and refuse anything but `AVAILABLE` with 409 `VEHICLE_UNAVAILABLE` | A truck VMMS just sent for maintenance is never dispatched |
| VMMS doesn't answer in 3 s, or answers 5xx: the list and the assignment answer 503 `FLEET_UNAVAILABLE` | No stale list is served and nothing is assigned |
| A 401 `TOKEN_EXPIRED`: one new token, one retry | Clock drift between containers |
| A vehicle VMMS answers 404 for shows as "Unavailable vehicle" and takes no new assignment | Old assignments keep their history |
| Two assignments racing for one truck keep dispatch's existing guard | Unchanged |

Dispatch only fields (required helpers, truck type, status remarks, the usual driver) live in BMS's own `vehicle_dispatch_profiles`, keyed by the VMMS `vehicle_id` with no foreign key. A vehicle with no profile row has `required_helpers` 0 and the rest null.

## Proving it

`node scripts/check-system.mjs bms --fleet` (or `vmms --fleet`) checks that every fleet route answers 401 with no token and 403 `WRONG_TOKEN_USE` with a user token, and that `GET /bms/config/vehicles` as `bms.ops@` lists the same plate numbers as `GET /vmms/vehicles` as `vmms.ops@`. That last check proves `fleet.read` end to end without the checker ever holding a client key.
