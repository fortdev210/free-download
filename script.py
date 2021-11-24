import click
import os

from base import BotManager
from settings import SPRINGER_LINK, SCI_HUB_LINK, ARTICLE_LINK


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
                discipline=self.discipline,
            )

            self.open_new_page()
            self.go_to_link(search_link)
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
                self.go_to_link(anchor)
                self.wait_element_loading("text=Cite this article")
                self.click_element("text=Cite this article")
                self.wait_element_loading('[data-track-action="view doi"]')

                content = """
                    ()=> {
                        return document.querySelector('[data-track-action="view doi"]').href
                    }
                """
                doi = self.page.evaluate(content)
                self.go_to_link(SCI_HUB_LINK)
                self.wait_element_loading('[type="textbox"]')
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
                filename = title + '.pdf'
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
        self.download_pdfs(results)
        print("Finished downloading.")


@click.command()
@click.option(
    "--start",
    default=2019,
    help="Start Year.",
    prompt="Input start year number, default is 2019.",
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
    default=3,
    help="End page to download",
    prompt="Input end page number, default is 3.",
)
@click.option(
    "--discipline",
    default="Chemistry",
    prompt="Input discipline, default is Environment",
    help="https://link.springer.com/search?date-facet-mode=between&query=recycling&facet-end-year=%7Bend_year%7D&facet-language=%22En%22&facet-start-year=%7Bstart_year%7D",
)
@click.option(
    "--query", default="catalyst", help="Query to download", prompt="Insert query"
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
        discipline='+'.join(discipline.split(' ')),
    )
    bot.run()


if __name__ == "__main__":
    main()
