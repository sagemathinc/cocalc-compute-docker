/*
This is an express handler that does the following:

- It checks to see if the cookie called AUTH_TOKEN is set to authToken,
  and if so it does nothing at all, letting other handlers deal.


- If AUTH_TOKEN is not set to authToken, it checks for a query parameter
  ?auth_token=..., and if it is set to authToken, it uses the "cookies"
  node module to set the cookie AU_TOKEN to authToken (with { secure: true }),,
  then returns letting other handlers further handle the route.

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

*/

import { Application, Request, Response, urlencoded } from "express";
import cookies from "cookies";
import cookieParser from "cookie-parser";

// HTML page that asks the user to paste the auth token
const signInPage = (req: Request, incorrectToken: boolean = false): string => `
  <form method="POST">
    ${
      incorrectToken
        ? '<p style="color: red;">Incorrect Authentication Token. Please try again.</p>'
        : ""
    }
    <input name="authToken" type="password" placeholder="Paste authentication token here"/>
    <input type="hidden" name="returnTo" value="${req.originalUrl}" />
    <input type="submit" value="Authentication Token"/>
  </form>
`;

// Main function
export default function createAuth(app: Application, authToken: string) {
  // Enable URL-encoded bodies
  app.use(urlencoded({ extended: true }));
  // Use the cookie-parser middleware so req.cookies is defined.
  app.use(cookieParser());

  const handle = (req: Request, res: Response, next) => {
    const reqAuthToken =
      req.body.authToken || req.query.auth_token || req.cookies.AUTH_TOKEN;
    const incorrectToken = req.method === "POST" && reqAuthToken !== authToken;

    if (reqAuthToken === authToken) {
      // if the token is correct
      if (req.cookies.AUTH_TOKEN != authToken) {
        // set cookie
        new cookies(req, res).set("AUTH_TOKEN", authToken, { secure: true });
      }
      if (req.method === "GET") {
        next();
      } else if (req.method === "POST") {
        res.redirect(req.body.returnTo || "/");
      }
    } else if (req.method === "POST") {
      // they just attempted to sign in
      if (incorrectToken) {
        // wrong token -- try again
        res.send(signInPage(req, incorrectToken));
      } else {
        // correct -- redirect them to the page they wanted to go to.
        res.redirect(req.body.returnTo || "/");
      }
    } else {
      // send them to sign in page
      res.send(signInPage(req));
    }
  };

  app.all("*", handle);
}
