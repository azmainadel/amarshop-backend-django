from django.http import HttpResponseForbidden

BLACKLIST = ['127.0.0.1', '192.168.1.1', '10.0.0.1']

class IPBlacklistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.blacklisted_ips = BLACKLIST
        
    def __call__(self, request):
        ip = self.get_client_ip(request)
        
        if ip in self.blacklisted_ips:
            return HttpResponseForbidden('Access Denied')
        
        return self.get_response(request)
        
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')