import dns.resolver
import socket
import whois
from concurrent.futures import ThreadPoolExecutor

class NetworkTools:
    @staticmethod
    def get_mx_records(domain):
        """Standard MX Lookup."""
        try:
            records = dns.resolver.resolve(domain, 'MX')
            sorted_records = sorted(records, key=lambda r: r.preference)
            return [(str(r.exchange).rstrip('.'), r.preference) for r in sorted_records]
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def get_dns_records(domain, record_type):
        """Generic DNS Lookup (A, AAAA, TXT, NS, CNAME)."""
        try:
            records = dns.resolver.resolve(domain, record_type)
            return [str(r) for r in records]
        except Exception as e:
            return [f"Error: {str(e)}"]

    @staticmethod
    def check_port(host, port, timeout=2):
        """Check if a TCP port is open."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    @staticmethod
    def scan_common_ports(host):
        """Scan common mail ports."""
        ports = {
            25: "SMTP",
            465: "SMTP (SSL)",
            587: "SMTP (TLS)",
            110: "POP3",
            995: "POP3 (SSL)",
            143: "IMAP",
            993: "IMAP (SSL)",
            80: "HTTP",
            443: "HTTPS"
        }
        results = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_port = {executor.submit(NetworkTools.check_port, host, port): port for port in ports}
            for future in future_to_port:
                port = future_to_port[future]
                is_open = future.result()
                results[port] = (ports[port], is_open)
        return results

    @staticmethod
    def check_rbl(ip_address):
        """Check IP against common Real-time Blackhole Lists (RBLs)."""
        rbls = [
            "zen.spamhaus.org",
            "bl.spamcop.net",
            "b.barracudacentral.org",
            "dnsbl.sorbs.net",
            "all.s5h.net",
            "noptr.spamrats.com"
        ]
        
        # Reverse IP for RBL query
        try:
            reversed_ip = ".".join(reversed(ip_address.split(".")))
        except ValueError:
            return {"Error": "Invalid IP Address"}

        results = {}
        
        def query_rbl(rbl_domain):
            query = f"{reversed_ip}.{rbl_domain}"
            try:
                dns.resolver.resolve(query, 'A')
                return True # Listed
            except dns.resolver.NXDOMAIN:
                return False # Not Listed
            except Exception:
                return None # Error/Timeout

        with ThreadPoolExecutor(max_workers=len(rbls)) as executor:
            future_to_rbl = {executor.submit(query_rbl, rbl): rbl for rbl in rbls}
            for future in future_to_rbl:
                rbl = future_to_rbl[future]
                results[rbl] = future.result()
        
        return results

    @staticmethod
    def get_whois(domain):
        """Get Whois information."""
        try:
            w = whois.whois(domain)
            return w
        except Exception as e:
            return str(e)
