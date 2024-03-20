/*
This is an express handler that does the following:

- Takes as input authTokenPath, which is the path to a file that
  contains an auth token.  If the file can't be read, then token is
  set to a random 128 crypto secure value, locking all users out of the site.
  If the file can be read, then that is the secret token (as utf8).
  If the file *changes* then all currently authenticated users must
  reauthenticate for their next http request, and the new token is used.

- It checks to see if the cookie called AUTH_TOKEN is set to authToken,
  and if so it does nothing at all, letting other handlers deal.

- If AUTH_TOKEN is not set to authToken, it checks for a query parameter
  ?auth_token=..., and if it is set to authToken, it uses the "cookies"
  node module to set the cookie AU_TOKEN to authToken (with { secure: true }),,
  then returns letting other handlers further handle the route.

- If AUTH_TOKEN is not set to app: Application, authToken and there is no query param handled above,
  it returns a simple sign in HTML page, with a form that requests that
  the user paste in the authToken.  This page also has a query parameter
  in it that encodes the page the user was trying to visit.  That will
  be used in the next step below.

- It also handles a POST request from the simple sign in HTML page, which
  receives the authToken, sets the cookie AUTH_TOKEN as above, and directs the
  user back to the page they were trying to open.

TODO: rate limiting, to slightly mitigate DOS attacks and/or brute force attacks.

*/

import cookies from "cookies";
import { readFile } from "fs/promises";
import debug from "debug";
import { randomBytes } from "crypto";
import { watch } from "chokidar";
import { debounce } from "lodash";

// it's important this isn't being used by any target of our proxy, or things could break.
export const AUTH_PATH = `/__cocalc_proxy_${Math.random()}`;
const POST_NAME = "cocalcProxyAuthToken";
export const COOKIE_NAME = "COCALC_COMPUTE_SERVER_AUTH_TOKEN";
const COCALC_AUTH_RETURN_TO = `cocalcReturnTo_${Math.random()}`;

const ChokidarOpts = {
  persistent: true,
  followSymlinks: false,
  disableGlobbing: true,
  depth: 0,
  ignorePermissionErrors: true,
} as const;

const log = debug("proxy:auth");

// Main function
export default async function enableAuth({
  router,
  authTokenPath,
}: {
  router;
  authTokenPath: string;
}) {
  const authToken = { current: randomBytes(128).toString("hex") };
  const updateAuthToken = async () => {
    try {
      authToken.current = (await readFile(authTokenPath)).toString().trim();
    } catch (err) {
      log(
        "WARNING -- unable to read auth token from ",
        authTokenPath,
        err,
        " so setting token to a long random string until path is available",
      );
      authToken.current = randomBytes(128).toString("hex");
    }
  };
  await updateAuthToken();
  const watcher = watch(authTokenPath, ChokidarOpts);
  watcher.on(
    "all",
    debounce(updateAuthToken, 1000, { leading: true, trailing: true }),
  );
  watcher.on("error", (err) => {
    log(`error watching authTokenPath '${authTokenPath}' -- ${err}`);
  });

  const isAuthCookieValid = (req) => {
    let auth = "";
    if (req.cookies != null) {
      auth = req.cookies[COOKIE_NAME];
    } else {
      // work even without cookie middleware -- used for websocket upgrade.
      for (const x of req.headers["cookie"].split(";")) {
        const [key, val] = x.split("=");
        if (key.trim() == COOKIE_NAME) {
          auth = val.trim();
          break;
        }
      }
    }
    return auth == authToken.current;
  };

  const handle = (req, res, next) => {
    const reqAuthToken =
      req.body?.[POST_NAME] || req.query.auth_token || req.cookies[COOKIE_NAME];

    if (reqAuthToken === authToken.current) {
      // the token is correct, but is the cookie -- if not, set the cookie
      if (!isAuthCookieValid(req)) {
        // but the cookie isn't, then they just authenticated, so we store
        // the correct cookie
        new cookies(req, res).set(COOKIE_NAME, authToken.current, {
          secure: true,
          httpOnly: true,
        });
        if (
          req.method === "POST" &&
          req.body?.[COCALC_AUTH_RETURN_TO] != null
        ) {
          // and also redirect them if they really did just authenticate via the form
          res.redirect(req.body[COCALC_AUTH_RETURN_TO]);
          return;
        }
      }
      next();
    } else {
      // token is NOT correct -- they messed up or need to be sent to the sign in page.
      if (req.method === "POST") {
        // they just attempted to sign in
        if (reqAuthToken !== authToken.current) {
          // wrong token -- try again
          res.send(signInPage(req, true, req.body?.[COCALC_AUTH_RETURN_TO]));
        } else {
          if (req.body?.[COCALC_AUTH_RETURN_TO] != null) {
            // correct -- redirect them to the page they wanted to go to.
            res.redirect(req.body?.[COCALC_AUTH_RETURN_TO]);
          }
        }
      } else {
        // send them to sign in page
        res.send(signInPage(req));
      }
    }
  };

  router.use("*", handle);
  return isAuthCookieValid;
}

// HTML page that asks the user to paste the auth token
const signInPage = (
  req,
  postSubmissionWithIncorrectToken: boolean = false,
  returnTo: string | undefined = undefined,
): string => `
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
  </head>
  <body>
    <div style="text-align: center; font-family: Arial, sans-serif; display: flex; justify-content: center; flex-direction: column; height: 100%;">
      <h1 style="color: #444;">Authentication Required</h1>
      ${
        postSubmissionWithIncorrectToken
          ? `<p style="color: red">Incorrect Authentication Token. Please try again.</p>`
          : `<p>Please enter the authentication token to proceed:</p>`
      }
      <form action="${AUTH_PATH}" method="POST" style="margin: 20px auto; display: inline-block;">
        <input name="${POST_NAME}" type="password" placeholder="Paste authentication token here..." style="padding: 6.5px 10px; width: 300px; margin-right: 10px; border-radius: 5px; border: 1px solid #ccc; font-size:12pt; margin-bottom:15px"/>
        <input type="hidden" name="${COCALC_AUTH_RETURN_TO}" value="${
          returnTo ?? req.originalUrl
        }" />
        <button type="submit" style="padding: 6.5px 15px; border-radius:5px; background-color: #007bff; color: white; border: none; cursor: pointer;font-size:12pt">Authenticate</button>
      </form>
    </div>
  </body>
`;

export function stripAuthCookie(cookie: string): string {
  if (cookie == null) {
    return cookie;
  }
  const v: string[] = [];
  for (const c of cookie.split(";")) {
    const z = c.split("=");
    if (z[0].trim() == COOKIE_NAME) {
      // do not include it in v, which will
      // be the new cookies values after going through
      // the proxy.
    } else {
      v.push(c);
    }
  }
  return v.join(";");
}
