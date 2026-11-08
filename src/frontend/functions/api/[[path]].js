
export async function onRequest({ request }) {
  const incomingUrl = new URL(request.url);
  const backendOrigin = "https://api.careerforgeapp.me";

  const targetUrl = new URL(
    incomingUrl.pathname + incomingUrl.search,
    backendOrigin
  );

  const upstreamRequest = new Request(targetUrl, request);
  const upstreamResponse = await fetch(upstreamRequest, {
    redirect: "manual",
  });

  const headers = new Headers(upstreamResponse.headers);
  const location = headers.get("Location");

  if (location) {
    const redirectUrl = new URL(location, targetUrl);

    if (redirectUrl.origin === backendOrigin) {
      headers.set(
        "Location",
        incomingUrl.origin +
          redirectUrl.pathname +
          redirectUrl.search +
          redirectUrl.hash
      );
    }
  }

  headers.set("Cache-Control", "no-store");

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers,
  });
}
