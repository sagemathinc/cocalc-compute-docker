/*
This is an express handler that does the following:

- It checks to see if the cookie called AUTH_TOKEN is set to authToken,
  and if so it does nothing at all, letting other handlers deal.

- If AUTH_TOKEN is not set to authToken, it checks for a query parameter
  ?auth_token=..., and if it is set to authToken, it uses the "cookies"
  node module to set the cookie AU_TOKEN to authToken (with { secure: true }),,
  then returns letting other handlers further handle the route.

- If AUTH_TOKEN is not set to app: Application, authToken and there is no query param handled above,
  and there is no query param handled above,
  it returns a simple sign in HTML page, with a form that requests that

  the user paste in the authToken.  This page also has a query parameter
  in it that encodes the page the user was trying to visit.  That will
  be used in the next step below.

- It also handles a POST request from the simple sign in HTML page, which
  receives the authToken, sets the cookie AUTH_TOKEN as above, and directs the
  user back to the page they were trying to open.

TODO: rate limiting, to slightly mittigate DOS attacks and/or brute force attacks.

*/

import cookies from "cookies";

// it's important this isn't being used by any target of our proxy, or things could break.
export const AUTH_PATH = `/__cocalc_proxy_${Math.random()}`;
const POST_NAME = "cocalcProxyAuthToken";
const COOKIE_NAME = "COCALC_PROXY_AUTH_TOKEN";

// Main function
export default function enableAuth({
  router,
  authToken,
}: {
  router;
  authToken: string;
}) {
  const handle = (req, res, next) => {
    const reqAuthToken =
      req.body?.[POST_NAME] || req.query.auth_token || req.cookies[COOKIE_NAME];

    if (reqAuthToken === authToken) {
      // the token is correct
      if (req.cookies[COOKIE_NAME] != authToken) {
        // but the cookie isn't, then they just authenticated, so we store
        // the correct cookie
        new cookies(req, res).set(COOKIE_NAME, authToken, {
          secure: true,
          httpOnly: true,
        });
        if (req.method === "POST") {
          // and also redirect them if they really did just authenticate via the form
          res.redirect(req.body.returnTo || "/");
          return;
        }
      }
      next();
    } else {
      // token is NOT correct -- they messed up or need to be sent to the sign in page.
      if (req.method === "POST") {
        // they just attempted to sign in
        if (reqAuthToken !== authToken) {
          // wrong token -- try again
          res.send(signInPage(req, true, req.body?.returnTo));
        } else {
          // correct -- redirect them to the page they wanted to go to.
          res.redirect(req.body.returnTo || "/");
        }
      } else {
        // send them to sign in page
        res.send(signInPage(req));
      }
    }
  };

  router.use("*", handle);
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
        <input type="hidden" name="returnTo" value="${
          returnTo ?? req.originalUrl
        }" />
        <button type="submit" style="padding: 6.5px 15px; border-radius:5px; background-color: #007bff; color: white; border: none; cursor: pointer;font-size:12pt">Authenticate</button>
      </form>
    </div>
  </body>
`;
