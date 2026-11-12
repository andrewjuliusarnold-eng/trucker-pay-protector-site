// "truckerpayprotector.com/account" and anything under it is an account page (the app's week sheet prints that
// address). The account site lives at account.truckerpayprotector.com. Used by /account/ and by the Page not found page.
if (/^\/account(\/|$)/i.test(location.pathname)) location.replace('https://account.truckerpayprotector.com/');
