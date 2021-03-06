# Copyright 2011, 2012 SRI International
# See LICENSE for other credits and copying information

# Copyright 2013 eQualit.ie under AGPL v3.0 or higher

# AUTHORS: Vmon: Initial version adopted from Stegotorus

import os
import os.path
import shutil
import subprocess
import sys #for argv

import unittest

from pdb import set_trace as tr

class BanjaxBehaviorTest(unittest.TestCase):

    BANNED_URL = "localhost/vmon"
    BANNED_MESSAGE = "<html><header></header><body>Forbidden</body></html>"
    #ATS_HOST = "127.0.0.1:8080"
    ATS_HOST = "localhost:8080"

    MAGIC_WORD      = "iloveyoumoinonplus"
    AUTH_COOKIE     = "deflect=m/FW19g3DzzDxDrC2eM+Zn+KsZP5fAmRAAAAAA==bNfg7zBaZHmqSwiLtvKpqzi4QFt/bknzYOmjjbaPhe8="
    BAD_AUTH_COOKIE = "deflect=DeeiSdkg/fu1w5hnq0p9V1A/fXawj5/TAAAAAAuwxyzabcdefghijklmnopqrstuvwxyz3uffRiGLQ60s="
    AUTH_PAGE       = "auth.html"
    CACHED_PAGE     = "cached_page.html"
    UNCACHED_PAGE   = "uncached_page.html"

    SOLVER_PAGE_PREFIX_LEN = 100;
    COMP_LEN = 100;

    ATS_INIT_DELAY = 6

    banjax_dir      = "/usr/local/trafficserver/modules/banjax"
    banjax_test_dir = "/root/dev/banjax/test"
    ats_bin_dir     = "/usr/local/trafficserver/bin"
    http_doc_root   = "/var/www"

    AUTH_CHALLENGE_CONFIG = (
        "challenger:\n"
        "    difficulty: 0\n"
        "    key: 'allwearesayingisgivewarachance'\n"
        "    challenges:\n"
        "      - name: 'example.co_auth'\n"
        "        domains:\n"
        "         - '"+ATS_HOST+"'\n"
        "        challenge_type: 'auth'\n"
        "        challenge: '"+AUTH_PAGE+"'\n"
        "        password_hash: 'BdZitmLkeNx6Pq9vKn6027jMWmp63pJJowigedwEdzM='\n"
        "        # sha256('howisbabbyformed?')\n"
        "        magic_word: '"+MAGIC_WORD+"'\n"
        "        magic_word_exceptions: ['wp-admin/admin.ajax.php']\n"
        "        validity_period: 120\n"
        "        no_of_fails_to_ban: 10\n");

    # Auxilary functions
    def read_page(self, page_filename):
        page_file  = open(BanjaxBehaviorTest.banjax_test_dir + "/"+ page_filename, 'rb')
        return page_file.read()

    def read_solver_body(self):
        solver_body = open(BanjaxBehaviorTest.banjax_dir + "/solver.html")
        self.SOLVER_PAGE_PREFIX = solver_body.read(self.SOLVER_PAGE_PREFIX_LEN)

    def restart_traffic_server(self):
        traffic_proc = subprocess.Popen([BanjaxBehaviorTest.ats_bin_dir + "/trafficserver", "restart"],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        traffic_proc.wait()
        import time
        time.sleep(BanjaxBehaviorTest.ATS_INIT_DELAY)
        self.assertEqual(traffic_proc.stderr.read(), "")
        return traffic_proc.stdout.read()

    def stop_traffic_server(self):
        traffic_proc = subprocess.Popen([BanjaxBehaviorTest.ats_bin_dir + "/trafficserver", "stop"],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        traffic_proc.wait()

    def replace_config(self, new_config_filename):
        shutil.copyfile(self.banjax_test_dir + "/" + new_config_filename , BanjaxBehaviorTest.banjax_dir + "/banjax.conf")
        #We need to restart ATS to make banjax to read the config again
        return self.restart_traffic_server()

    def replace_config2(self, config_string):
        config_path = BanjaxBehaviorTest.banjax_dir + "/banjax.conf"
        config = open(config_path, 'w')
        config.write(config_string)
        config.close()
        #We need to restart ATS to make banjax to read the config again
        return self.restart_traffic_server()

    def put_page(self, page_filename):
        shutil.copyfile(BanjaxBehaviorTest.banjax_test_dir + "/" + page_filename, BanjaxBehaviorTest.http_doc_root + "/" +page_filename)

    def replace_page(self, page_old, page_new):
        shutil.copyfile(BanjaxBehaviorTest.banjax_test_dir + "/" + page_new, BanjaxBehaviorTest.http_doc_root + "/" +page_old)

    def write_page(self, page_name, content):
        page = open(BanjaxBehaviorTest.http_doc_root + "/" + page_name, 'w')
        page.write(content)
        page.close()

    def do_curl(self, url, cookie = None):
        curl_cmd = ["curl", url] + (cookie and ["--cookie", cookie] or [])
        curl_proc = subprocess.Popen(curl_cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

        return curl_proc.stdout.read()

    def setUp(self):
        self.read_solver_body()

    def tearDown(self):
        self.stop_traffic_server()

    def ntest_request_banned_url(self):
        self.replace_config("banned_url_test.conf")
        result = self.do_curl(self.BanjaxBehaviorTest.BANNED_URL)
        self.assertEqual(result,self.BANNED_MESSAGE);

    def ntest_unbanned_challenged_url(self):
        self.replace_config("challenged_url_test.conf")
        result = self.do_curl(ALLOWED_URL)
        self.assertEqual(result[0:self.SOLVER_PAGE_PREFIX_LEN],self.SOLVER_PAGE_PREFIX);

    def ntest_unchallenged_white_listed_ip(self):
        tr()
        self.replace_config("white_listed.conf")
        result = self.do_curl(BanjaxBehaviorTest.BANNED_URL)
        self.assertEqual(result,self.ALLOWED_PAGE);

    def test_auth_challenged_success(self):
        """
        This test simulate a correct password entered in the auth page
        after entring the password it checks that ATS serves directly
        from origin everytime
        """
        #Auth page
        self.replace_config2(self.AUTH_CHALLENGE_CONFIG)
        result = self.do_curl(BanjaxBehaviorTest.ATS_HOST + "/" +BanjaxBehaviorTest.MAGIC_WORD)
        self.assertEqual(result[:BanjaxBehaviorTest.COMP_LEN],self.read_page(BanjaxBehaviorTest.AUTH_PAGE)[:BanjaxBehaviorTest.COMP_LEN]);

        #request to guarantee cache if fails
        self.put_page(BanjaxBehaviorTest.CACHED_PAGE)
        result = self.do_curl(BanjaxBehaviorTest.ATS_HOST + "/" + BanjaxBehaviorTest.CACHED_PAGE, cookie = BanjaxBehaviorTest.AUTH_COOKIE)
        self.assertEqual(result, self.read_page(BanjaxBehaviorTest.CACHED_PAGE))

        #check if it is not cached
        self.replace_page(BanjaxBehaviorTest.CACHED_PAGE,BanjaxBehaviorTest.UNCACHED_PAGE)
        result = self.do_curl(BanjaxBehaviorTest.ATS_HOST + "/" + BanjaxBehaviorTest.CACHED_PAGE, cookie = BanjaxBehaviorTest.AUTH_COOKIE)
        self.assertEqual(result,self.read_page(BanjaxBehaviorTest.UNCACHED_PAGE));

        #check that the nocache reply is not cached
        self.replace_page(BanjaxBehaviorTest.CACHED_PAGE,BanjaxBehaviorTest.CACHED_PAGE)
        result = self.do_curl(BanjaxBehaviorTest.ATS_HOST + "/" + BanjaxBehaviorTest.CACHED_PAGE, cookie = BanjaxBehaviorTest.AUTH_COOKIE)
        self.assertEqual(result,self.read_page(BanjaxBehaviorTest.CACHED_PAGE));



    def test_auth_challenged_failure(self):
        """
        The test simulate entering a wrong password in the auth challenge
        a banned message is expected to be served
        """
        # NOTE: This test requires the records.config option 'required_headers' set to zero
        #       CONFIG proxy.config.http.cache.required_headers INT 0

        # TODO: This test sometimes fails because the first time a page is downloaded
        #       it is already cached. So figure out how to clear the cache on the
        #       traffic server before the below code is executed.
        #       NOTE: TS v7.2 this can be done with `traffic_ctl server --clear-cache`
        #             but I haven't yet found a way how to do it with previous versions.
        page       = BanjaxBehaviorTest.CACHED_PAGE
        host       = BanjaxBehaviorTest.ATS_HOST
        bad_cookie = BanjaxBehaviorTest.BAD_AUTH_COOKIE

        def html(body):
            return "<html><body>" + body + "</body></html>"

        self.replace_config2(self.AUTH_CHALLENGE_CONFIG)

        #request to guarantee cache
        self.write_page(page, html("body 0"))
        result = self.do_curl(host + "/" + page, cookie = bad_cookie)
        self.assertEqual(result, html("body 0"))

        #check if it is reading from cache if the cookie is bad
        self.write_page(page, html("body 1"))
        result = self.do_curl(host + "/" + page, cookie = bad_cookie)
        self.assertEqual(result, html("body 0"))


    def test_auth_challenged_unchallenged_cached(self):
        """
        This test request a website with auth challenge but it does
        not invoke the magic word, hence ATS should serve the page
        through cache consitantly
        """
        self.replace_config2(self.AUTH_CHALLENGE_CONFIG)

        self.put_page(BanjaxBehaviorTest.CACHED_PAGE)
        result = self.do_curl(BanjaxBehaviorTest.ATS_HOST + "/" + BanjaxBehaviorTest.CACHED_PAGE)
        self.assertEqual(result, self.read_page(BanjaxBehaviorTest.CACHED_PAGE))

        self.replace_page(BanjaxBehaviorTest.CACHED_PAGE,BanjaxBehaviorTest.UNCACHED_PAGE)
        result = self.do_curl(BanjaxBehaviorTest.ATS_HOST + "/" + BanjaxBehaviorTest.CACHED_PAGE)
        self.assertEqual(result,self.read_page(BanjaxBehaviorTest.CACHED_PAGE));

if __name__ == '__main__':
    from unittest import main
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--banjax-dir', default=BanjaxBehaviorTest.banjax_dir)
    parser.add_argument('--banjax-test-dir', default=os.getcwd())
    parser.add_argument('--ats-bin-dir', default=BanjaxBehaviorTest.ats_bin_dir)
    parser.add_argument('--http-doc-root', default=BanjaxBehaviorTest.http_doc_root)
    parser.add_argument('unittest_args', nargs='*')

    args = parser.parse_args()
    BanjaxBehaviorTest.banjax_dir      = args.banjax_dir
    BanjaxBehaviorTest.banjax_test_dir = args.banjax_test_dir
    BanjaxBehaviorTest.http_doc_root   = args.http_doc_root
    BanjaxBehaviorTest.ats_bin_dir     = args.ats_bin_dir

    # Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
    sys.argv[1:] = args.unittest_args
    unittest.main()
    main()
