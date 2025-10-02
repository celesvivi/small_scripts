import pyperclip, yaml_config, os, sys, time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from mLog import Logger, TypeOfLog
# VERSION 1.0
# Need mLog and yaml_config from the modular page (https://github.com/celesvivi/modular) if you want to pyinstaller this script
# Yes there is a lot of redundant parts but idrc, will fix it in a later date
def get_app_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
    
class URL_cleaner:
    def __init__(self):
        self.log_instance = Logger(get_app_directory())

        self.default_config = {
            'tracking_params': [
                # Facebook/Meta
                    'fbclid', 'fb_action_ids', 'fb_action_types', 'fb_ref', 'fb_source',
                    'fb_comment_id', 'comment_tracking', 'notif_id', 'notif_t',
                
                # Google Analytics & Ads  
                    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                    'utm_id', 'utm_source_platform', 'utm_creative_format', 'utm_marketing_tactic',
                    'gclid', 'gclsrc', 'dclid', 'gbraid', 'wbraid', '_ga', '_gl',
                
                # Twitter/X
                    't', 's', 'ref_src', 'ref_url', 'twclid', 'twitter-impression-id',
                
                # YouTube
                    'feature', 'kw', 'si', 'app', 'persist_app', 'noapp', 'has_verified',
                    'list', 'index', 'pp', 'source_ve_path', 'ab_channel', 'autoplay',

                # Others
                    'msclkid', 'cvid', 'trk', 'trkInfo', 'li_fat_id', 'lipi',
                    'utm_name', 'rdt_cid', 'share_id', 'context',
                    'is_copy_url', 'sender_device', 'sender_web_id', 'tt_from',
                    'igshid', 'igsh', 'img_index', 'amp_analytics',
                    'mc_cid', 'mc_eid', 'yclid', 'ncid', '_hsenc', '_hsmi'
            ],
            'supported_domains': [
                'facebook.com', 'fb.com', 'm.facebook.com',
                'twitter.com', 'x.com', 'mobile.twitter.com', 'fxtwitter.com', 'vxtwitter.com',
                'youtube.com', 'youtu.be', 'm.youtube.com',
                'instagram.com', 'm.instagram.com',
                'linkedin.com', 'm.linkedin.com',
                'reddit.com', 'old.reddit.com',
                'pixiv.com'
            ],
            'domain_to_name': {
                'youtube': ['youtube.com', 'youtu.be', 'm.youtube.com'],
                'twitter': ['twitter.com', 'x.com', 'mobile.twitter.com', 'vxtwitter.com'],
                'pixiv': ['pixiv.net']
            },
            'convertible_domains': [
                'twitter', 'pixiv'
            ],
            'convert_conditions': {
                'twitter': ['status'],
                'pixiv': ['artworks']
            },
            'convertion_domains': {
                'twitter': ['fxtwitter.com'],
                'pixiv': ['phixiv.net']
            },
            'exclusion_params': {
                'youtube': ['t']
            }

        }
        self.config = yaml_config.Config(get_app_directory(), self.default_config, self.log)
        self.last_clipboard = ""
    def log(self, message: str, log_type: str = "info"):
        self.log_instance.log(message, log_type)

    def load_config(self): #Surely there is a better way to automatically do this
        self.tracking_params = self.config.get_variable('tracking_params')
        self.supported_domains = self.config.get_variable('supported_domains')
        self.domain_to_name = self.config.get_variable('domain_to_name')
        self.convertible_domains = self.config.get_variable('convertible_domains')
        self.convert_conditions = self.config.get_variable('convert_conditions')
        self.convertion_domains = self.config.get_variable('convertion_domains')
        self.exclusion_params = self.config.get_variable('exclusion_params')

    def get_domain(self, url):
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    def turn_into_readable_domain(self, domain):
        domain_to_name = self.domain_to_name
        for key, values in domain_to_name.items():
            if domain in values:
                return key


    def is_url(self, string):
        if not (isinstance(string, str)):
            return False
        parsed = urlparse(string)
        if all([parsed.scheme in ('http', 'https'), parsed.netloc, len(string) < 200, len(string) > 5]):
            self.log(f"This is an url {string}", TypeOfLog.INFO)
            return True
        self.log(f"This is not an url {string}", TypeOfLog.INFO)
        return False
    
    def is_supported_domains(self, url):
        domain = self.get_domain(url)
        if (any(platform == domain or domain.endswith('.' + platform) 
                   for platform in self.supported_domains)):
            self.log("This domain is supported", TypeOfLog.INFO)
            return True
        self.log("This domain is not supported", TypeOfLog.INFO)
        return False

    def is_convertable_url(self, url):
        readable_domain = self.turn_into_readable_domain(self.get_domain(url))
        if readable_domain in self.convertible_domains:
            self.log("This domain is convertible", TypeOfLog.INFO)
            return True
        else:
            self.log("This domain is not convertible", TypeOfLog.INFO)
            return False

    def is_convert_condition(self, url):
        path = urlparse(url).path
        readable_domain = self.turn_into_readable_domain(self.get_domain(url))
        conditions = self.config.get_variable(f'convert_conditions.{readable_domain}')
        return any(condition in path for condition in conditions)
    
    def get_converted_domain(self, readable_domain):
        return self.config.get_variable(f'convertion_domains.{readable_domain}')
    
    def get_exclusion(self, readable_domain):
        return self.config.get_variable(f'exclusion_params.{readable_domain}')

    def is_exclusion(self, url):
        domain = self.turn_into_readable_domain(self.get_domain(url))
        return domain in self.exclusion_params
    
    def convert_url(self, url):
        parsed = urlparse(url)
        readable_domain = self.turn_into_readable_domain(self.get_domain(url))   
        converted_domain = self.get_converted_domain(readable_domain)[0]
        converted_url = urlunparse((
            parsed.scheme,
            converted_domain,
            parsed.path, 
            parsed.params, 
            parsed.query, 
            parsed.fragment))
        self.log(f"Convert {self.get_domain(url)} to {converted_domain}",TypeOfLog.ACTION)
        return converted_url

    def clean_url(self, url):
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        clean_query = {}
        dirty_query = {}

        for param, values in query_params.items():
            if (self.is_exclusion(url) and param in self.get_exclusion(url) 
                or 
                param not in self.tracking_params):
                clean_query[param] = values
            else:
                dirty_query[param] = values
        self.log(f"Clean {str(dirty_query)} out of url",TypeOfLog.ACTION)
        cleaned_url = urlunparse((
                parsed.scheme, 
                parsed.netloc, 
                parsed.path,
                parsed.params, 
                urlencode(clean_query, doseq=True),
                parsed.fragment
            ))
        return cleaned_url
    
    def process_clipboard(self, current): #HOLY NESTED CODE
        if self.is_url(current):
            final_url = None
            if self.is_supported_domains(current):
                cleaned = True
                final_url = self.clean_url(current)
                if self.is_convertable_url(current) and self.is_convert_condition(current):
                    if cleaned:
                        final_url = self.convert_url(final_url)
                    else: final_url = self.convert_url(current)
            if final_url is not None:
                pyperclip.copy(final_url)
                self.last_clipboard = final_url

    def checking_clipboard(self):
        while 1:
            tmp = pyperclip.paste()
            if tmp != self.last_clipboard:
                self.last_clipboard = tmp
                self.process_clipboard(tmp)
            time.sleep(0.35)

def main():
    cleaner = URL_cleaner()
    cleaner.load_config()
    cleaner.checking_clipboard()

if __name__ == '__main__':
    main()

