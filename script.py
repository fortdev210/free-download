import click
import os
import re
from googletrans import Translator
from base import BotManager
from settings import SPRINGER_LINK, SCI_HUB_LINK, ARTICLE_LINK
from api import get_proxy_ips

translator = Translator()

class Downloader(BotManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.topic = kwargs.get("topic")
        self.start = kwargs.get("start")
        self.end = kwargs.get("end")
        self.page_number = kwargs.get("page")
        self.page_range = kwargs.get("page_range")
        self.query = kwargs.get("search_key")
        self.discipline = kwargs.get("discipline")
        self.proxies = kwargs.get("proxies")

    def open_springer(self):
        if self.browser is None:
            self.create_browser()
        self.open_new_page()
        # self.go_to_link(SPRINGER_LINK)

    def select_topic(self):
        self.wait_element_loading('[id="Discipline"]')
        self.click_element(f"text={self.topic}")
        self.sleep(3)
        self.wait_element_loading('[id="date-facet"]')

    def filter_by_date_article(self):
        self.click_element("text=Date Published")
        self.sleep(1)
        self.wait_element_loading('[id="start-year"]')
        self.reinsert_value('[id="start-year"]', 2019)
        self.sleep(1)
        self.reinsert_value('[id="end-year"]', 2022)
        self.sleep(1)
        self.click_element('[id="date-facet-submit"]')
        self.wait_element_loading('[id="content-type-facet"]')

    def get_search_results(self):
        ## article link https://link.springer.com/search?date-facet-mode=between&facet-start-year=2019&facet-content-type=%22Article%22&facet-discipline=%22Materials+Science%22&facet-end-year=2022
        # self.wait_element_loading('[id="results-list"]')
        link_results = []
        title_results = []
        for page_number in self.page_range:
            search_link = ARTICLE_LINK.format(
                page=page_number,
                start=self.start,
                end=self.end,
                query=self.query,
                discipline='+'.join(self.discipline.split(' '))
            )

            self.open_new_page()
            self.go_to_link(search_link)
            try:
                self.wait_element_loading('[id="results-list"]')
                content = """() => {
                    let links = []
                    let titles = []
                    const lists = document.querySelector('[id="results-list"]').querySelectorAll('li')
                    for (let i=0; i<lists.length; i ++) {
                        list = lists[i]
                        anchor = list.querySelector('a').href
                        title = list.querySelector('a').innerText
                        links.push(anchor)
                        titles.push(title)
                    }
                    return [links, titles]
                }
                """
                page_results = self.page.evaluate(content)
                link_results = link_results + page_results[0]
                title_results = title_results + page_results[1]
                self.page.close()
            except Exception as e:
                self.page.close()
        return [link_results, title_results]

    def download_pdfs(self, results):
        success_number = 0
        anchor_list = results[0]
        title_list = results[1]
        
        for i in range(len(anchor_list)):
            anchor = anchor_list[i]
            title = title_list[i]
            try:
                self.open_new_page()
                print("anchor: " + anchor)
                self.go_to_link(anchor)
                self.wait_element_loading("text=Cite this article")
                self.click_element("text=Cite this article")
                self.wait_element_loading('[class="c-bibliographic-information__value"]')

                content = """
                    ()=> {
                        return document.querySelector('[class*="c-bibliographic-information__list-item--doi"]').querySelector('[class="c-bibliographic-information__value"]').innerText
                    }
                """
                doi = self.page.evaluate(content)
                print(doi)
                self.go_to_link(SCI_HUB_LINK)
                self.wait_element_loading('[type="textbox"]', 30000)
                self.insert_value('[type="textbox"]', doi)
                self.sleep(1)
                self.hit_enter()
                self.sleep(10)

                with self.page.expect_download() as download_info:
                    content = """
                        ()=>{
                            document.querySelector('#buttons').querySelector('button').click()
                        }
                    """
                    self.page.evaluate(content)
                download = download_info.value
                title = re.sub('[^A-Za-z0-9]+',' ', title)
                translated = translator.translate(title, dest='ko')
                filename = translated.text + '.pdf'
                download.save_as(filename)
                os.replace(os.path.join(os.getcwd(), filename),self.discipline + "/" + self.query + "/" + filename)
                self.page.close()
                success_number = success_number + 1
            except Exception as e:
                print("error", e)
                self.page.close()
        print(f"Total {len(anchor_list)}, success: {success_number}")

    def run(self):
        self.open_springer()
        results = self.get_search_results()
        if len(results[0]):
            total = len(results[0])
            print(f"Total search results: {total}, Downloading...")
            self.download_pdfs(results)
            print("Finished downloading.")
        else:
            print("No search results. Just change query or discipline.")


@click.command()
@click.option(
    "--start",
    default=2021,
    help="Start Year.",
    prompt="Input start year number, default is 2021.",
)
@click.option(
    "--end", default=2022, help="End Year.", prompt="Input end year, default is 2022."
)
@click.option(
    "--start_page",
    default=1,
    help="Start page to download",
    prompt="Input start page number, default is 1.",
)
@click.option(
    "--end_page",
    default=10,
    help="End page to download",
    prompt="Input end page number, default is 10.",
)
@click.option(
    "--discipline",
    default="Engineering",
    prompt="Input discipline, default is Environment",
    help="https://link.springer.com/search?date-facet-mode=between&query=recycling&facet-end-year=%7Bend_year%7D&facet-language=%22En%22&facet-start-year=%7Bstart_year%7D",
)
@click.option(
    "--query", default="construct machine", help="Query to download", prompt="Insert query"
)
def main(start, end, start_page, end_page, query, discipline):
    try:
        os.makedirs(discipline + '/' + query)
    except:
        pass

    bot = Downloader(
        start=start,
        end=end,
        use_chrome=False,
        page_range=range(start_page, end_page),
        search_key=query,
        discipline=discipline,
    )
    proxies = get_proxy_ips('W', 8889)
    print(proxies)
    bot.run()


if __name__ == "__main__":
    main()
