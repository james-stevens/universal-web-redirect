# Universal Web Redirect, via DNS

This server provides a unversal HTTP redirection service based on the [`URI` DNS Recource Record](https://en.wikipedia.org/wiki/URI_record).

As this RR seems to have been otherwise unsed to date (2023-05-02), many DNS maintenance systems do not support
the ability to for users to specify `URI` RR types. For this reason this server will fall back to looking for `TXT` records
which have almost universal support.

Performance will be slightly better if you use `URI` records, if you can, becuase it looks for these first.


## Setting up UWR on your domain

If you have an otherwise unused domain, do the following

1. Set your domain to point to one or more UWR nodes (public servers running this software)

	For example, if there is a public UWR node running at `10.11.12.111` (there won't be!), add the following
	records to your domain

		@ IN A 10.11.12.111
		* IN A 10.11.12.111

2. Now all `HTTP` requests for all hostname in your domain will go to the UWR node, so all you need
to do now is start adding UWR records wherever you want them.

	For example, if your twitter account is `https://twitter.com/JohnDeoTheThird`, then add the record

		_http._tcp.twt IN URL 1 1 "https://twitter.com/JohnDeoTheThird"

	If your DNS provider does not support `URL` record types, use a `TXT` record instead

		_http._tcp.twt IN TXT "https://twitter.com/JohnDeo"

	To set a UWR for the domain itself, set the following

		_http._tcp IN URL 1 1 "https://www.our-web-site.com/"

	or

		_http._tcp IN TXT "https://www.our-web-site.com/"

If these UWR records were set on the domain `example.com`, then the following web redirections would work

	http://example.com/ -> https://www.our-web-site.com/
	http://twt.example.com/ -> https://twitter.com/JohnDeoTheThird

So, when any user clicks the URL `example.com` they will be automatically redirected to `https://www.our-web-site.com/`.

If you only want to use UWR for certain names, you can choose to point only those names to the UWR node(s). For example

	twt IN A 10.11.12.111

With only this address record, instead of the address pair above, UWR would only be active on the hostname `twt`.

For fail-over / load-balancing, you can point to multiple UWR nodes by specifying multiple IP Addresses. For example

	@ IN A 10.11.12.111
	@ IN A 10.11.12.222
	* IN A 10.11.12.111
	* IN A 10.11.12.222

or

	twt IN A 10.11.12.111
	twt IN A 10.11.12.222


## Using CNAME records

Assuming you UWR service provider have given a name to their UWR service, you can also set a host name as a UWR name by using a `CNAME` record. For example,

	twt IN CNAME uwr.service-provider.net.

or

	* IN CNAME uwr.service-provider.net.


## CNAME vs A records

To make a specific host name a UWR name, you can use either a `CNAME` or `A` record. Both work slightly differently, so 
have slightly different pros & cons. Both work fine with individual host names or the wild card name, although it should be noted
that setting a `CNAME` on the wildcard host name may trigger unexpected results.

### CNAME - Pros
- Easier to understand & remember
- The UWR node service provider can move it to a new IP Address with no problems
- The UWR node service provider can implement geo-targetted load-balancing

### CNAME - Cons
- You *CAN NOT* put a `CNAME` record on the domain itself, so to use the domain itself as a UWR name, you must use `A` records
- A `CNAME` can only point to one UWR node service provider, where as you can use multiple `A` records to point to multiple UWR node service providers



## NOTES

1. For records of type `URI` the fields `priority` and `weight` are not (yet) implemented.

2. Where only one URL is given an `HTTP 301 Redirect` is given.
Where more than one URL is given one URL is picked at random and an `HTTP 302 Redirect` is given.

3. Becuase you can't have different IP addresses for different protocols, pointing a hostname to a UWR node means that hostname can **only** be used for UWR.
For example, HTTPS will still resolve to the UWR's IP Address, but will not work.

4. UWR does **NOT** support HTTPS, for lots of reasons. In fact UWR **ONLY** supports HTTP, nothing else.

5. UWR **will** support non-ICANN domain naming system, but ONLY if **BOTH** the user's browser and UWR node(s) can resolve the non-ICANN domain names.

6. If a hostname resolves to the IP of a UWR node, but the node can't find an exact match `URI` or `TXT` record for that hostname,
it will then look for a record at the hostname `_any.<domain>`. This is so users can have a default matching URL when using the wild card hostname.

7. Any remaining TTL of the DNS record is sent to the browser as `Cache-Control: max-age=<TTL>`, telling the browser the maximum time it can hold that redirect in cache.

8. The default behaviour is to forward the user to only the URL supplied, but if you wish to copy the path of the source URL onto the end of the
destination URL, you can specify this by adding the suffix `/$$` to the end of the destination URL. For example

			_http._tcp IN URL 1 1 "https://www.our-web-site.com/$$"

	With this in place, the URL

			http://example.com/user/login

	will be rediected to

			https://www.our-web-site.com/user/login


## Running your own UWR Node

To run your own UWR node, simple run this container on a public IP Address, port 80.

You can either build this container from its soruce code by running `./dkmk` in this directory, or use the
container `jamesstevens/universal-web-redirect` from `docker.com`.

When you run the container the environment variable `NAME_SERVERS`
must be set to a space separated list of the resolving name servers you wish the container to use.

NOTE: for improved perfomance, the container internally runs a copy of ISC's `bind` DNS Resolver, but it is configured to **ONLY**
get answers from the resolving name servers you specify. However, it will cache answers and do load-balancing & fail-over if you specify
multiple resolving name servers.



## Suggestions for Different TLAs for different sites

If everybody uses the same three letter prefix for each well known service provider, e.g. `twt` for Twitter, this could become a universal way to find
somebody's social media account, once you know their personal domain name.

Here's some suggestions

| TLA | Service |
| --- | ------- |
| twt | Twitter |
| fbk | Facebook |
| tkk | TikTok |
| ins | Instagram |
| ytb | YouTube |
| lnk | LinkedIn |
| pin | Pintrest |
| red | Reddit |

