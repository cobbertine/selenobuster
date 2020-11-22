import selenium.webdriver.firefox
import concurrent.futures
import argparse
import time
import os
import signal

class PAGE_STATUS:
    EXISTS = 2
    NOT_EXISTS = 4
    UNKNOWN = 8

    STRING_DICTIONARY = {EXISTS : "EXISTS", NOT_EXISTS : "NOT_EXISTS", UNKNOWN : "UNKNOWN"}

  
# Returns True if page exists, False otherwise.
def check_website(url, page, xpath_error_element, xpath_error_element_text_content, load_wait_time, cookies, proxy):
    def handle_timeout(browser, process_id):
        try:
            while(True):
                os.kill(process_id, signal.SIGKILL)
                # This will cause an exception once the process is dead.
                browser.title
                time.sleep(1)
        except:
            return(PAGE_STATUS.UNKNOWN, page)

    # Browser options for the Firefox engine (can see all options in any Firefox session with about:config)
    browser_options = selenium.webdriver.firefox.options.Options()
    # No visible window
    browser_options.headless = True

    browser_profile = selenium.webdriver.firefox.firefox_profile.FirefoxProfile()
    browser_profile.set_preference("browser.cache.disk.enable", False)
    browser_profile.set_preference("browser.cache.memory.enable", False)
    browser_profile.set_preference("browser.cache.offline.enable", False)
    browser_profile.set_preference("network.http.use-cache", False) 

    if len(proxy) > 0:
        # https://www.selenium.dev/documentation/en/webdriver/http_proxies/
        selenium.webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
        "httpProxy": proxy,
        "ftpProxy": proxy,
        "sslProxy": proxy,
        "proxyType": "MANUAL",
        }

    browser = selenium.webdriver.firefox.webdriver.WebDriver(options=browser_options, firefox_profile=browser_profile, proxy=proxy)
    browser.set_page_load_timeout(load_wait_time * 2)
    process_id = browser.desired_capabilities["moz:processID"]

    # Cookies can only be added when the browser is on the target URL.
    # Two requests are therefore needed to set the cookies and then use the cookies.
    if len(cookies) > 0:
        try:
            browser.get(url)
        except selenium.common.exceptions.TimeoutException:
            return handle_timeout(browser, process_id)

        for k,v in [cookie.split(":") for cookie in cookies.split(";")]:
            browser.add_cookie({"name" : k, "value": v}) 

    try:
        browser.get(url + page)
    except selenium.common.exceptions.TimeoutException:
        return handle_timeout(browser, process_id)

    time.sleep(load_wait_time)
    error_elements = browser.find_elements_by_xpath(xpath_error_element)

    if len(error_elements) > 0:
        if len(xpath_error_element_text_content) > 0:
            for error_element in error_elements:
                if error_element.get_attribute("textContent") == xpath_error_element_text_content:
                    # Error XPath was found, and specified string was found, so page does not exist.
                    browser.quit()
                    return (PAGE_STATUS.NOT_EXISTS, page)
            # Error XPath was found, BUT specified string was NOT found, so page does exist
            browser.quit()
            return (PAGE_STATUS.EXISTS, page)
        # Error XPath was found, no string was specified, so page does not exist.
        browser.quit()
        return (PAGE_STATUS.NOT_EXISTS, page)
    else:
        # Error Xpath was not found, so page does exist.
        browser.quit()
        return (PAGE_STATUS.EXISTS, page)

def initiate_workers(worker_args, word_list, threads):
    worker_args = worker_args.copy()
    worker_pool = concurrent.futures.ProcessPoolExecutor(max_workers=threads)
    workers = list()
    with open(os.path.abspath(word_list), mode="r") as website_page_list:
        for website_page in website_page_list:
            website_page = website_page.rstrip()
            if len(website_page) > 0:
                if "/" in website_page:
                    website_page = website_page.replace("/", "") + "/" if website_page[-1] == "/" else website_page.replace("/", "")
                worker_args["page"] = website_page
                workers.append(worker_pool.submit(check_website, **worker_args))
    return workers 

def handle_results(workers):
    try:
        for completed_worker in concurrent.futures.as_completed(workers):
            result = completed_worker.result()
            page_status = result[0]
            output_string = "{page} = {status}\n".format(page=result[1], status=PAGE_STATUS.STRING_DICTIONARY[page_status])
            if page_status == PAGE_STATUS.EXISTS or page_status == PAGE_STATUS.UNKNOWN:
                with open(RESULT_FILE_PATH, "a") as result_file:
                    result_file.write(output_string)
            print(output_string[:-1])
    except KeyboardInterrupt:
        print("User quit. Attempting to close safely...")
        for worker in workers:
            worker.cancel()
        while True:
            time.sleep(LOAD_WAIT_TIME)
            for worker in workers:
                if worker.running():
                    continue
            print("All workers have stopped. Closing...")
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatically check if page exists")
    parser.add_argument("url", type=str, default="")
    parser.add_argument("word_list", type=str, default="")    
    parser.add_argument("error_xpath", type=str, default="")
    parser.add_argument("-s", metavar="error_xpath_text_content", type=str, default="", help="Optional argument which will check if the provided error_xpath contains the provided string.")
    parser.add_argument("-l", metavar="load_wait_time", type=int, default=5, help="How long should the script wait for the error_xpath element to appear before making a decision. Defaults to 5 seconds.")
    parser.add_argument("-c", metavar="cookies" , type=str, default="")    
    parser.add_argument("-p", metavar="http_proxy", type=str, default="", help="Takes a string of the form host:port. Do not include the protocol.")    
    parser.add_argument("-t", metavar="threads", type=int, default=1, help="Defaults to 1 thread.")
    parser.add_argument("-o", metavar="result_file_path", type=str, default="results.txt", help="Defaults to results.txt in the current directory.")

    args = parser.parse_args()

    URL = args.url if args.url[-1] == "/" else args.url + "/"
    WORD_LIST = args.word_list    
    XPATH_ERROR_ELEMENT = args.error_xpath
    XPATH_ERROR_ELEMENT_TEXT_CONTENT = args.s
    LOAD_WAIT_TIME = args.l
    COOKIES = args.c
    PROXY = args.p
    THREADS = args.t
    RESULT_FILE_PATH = args.o

    worker_args = { "url" : URL, "xpath_error_element" : XPATH_ERROR_ELEMENT, "xpath_error_element_text_content" : XPATH_ERROR_ELEMENT_TEXT_CONTENT, "load_wait_time" : LOAD_WAIT_TIME, "cookies" : COOKIES, "proxy" : PROXY }

    workers = initiate_workers(worker_args, WORD_LIST, THREADS)
    handle_results(workers)