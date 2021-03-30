from rotating_proxies.policy import BanDetectionPolicy


class MyBanPolicy(BanDetectionPolicy):
    def response_is_ban(self, request, response):
        ban = super(MyBanPolicy, self).response_is_ban(request, response)
        ban = ban or b'Digit-Eyes' not in response.body
        return ban

    # def exception_is_ban(self, request, exception):
    #     # override method completely: don't take exceptions in account
    #     return None
