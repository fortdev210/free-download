import click

from base import BotManager
from settings import SPRINGER_LINK, SCI_HUB_LINK, ARTICLE_LINK


class Downloader(BotManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.topic = kwargs.get("topic")
        self.start = kwargs.get("start")
        self.end = kwargs.get("end")
        self.page_number = kwargs.get("page")
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

        search_link = ARTICLE_LINK.format(
            page=self.page_number,
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
            const lists = document.querySelector('[id="results-list"]').querySelectorAll('li')
            for (let i=0; i<lists.length; i ++) {
                list = lists[i]
                anchor = list.querySelector('a').href
                links.push(anchor)
            }
            return links
        }
        """
        results = self.page.evaluate(content)
        self.page.close()
        return results

    def download_pdfs(self, anchor_list):
        for anchor in anchor_list:
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
                print(doi)
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
                path = download.path()
                print(path)
                download.save_as(download.suggested_filename)
                self.sleep(10)
                self.page.close()
            except Exception as e:
                print("error", e)
                self.page.close()

    def run(self):
        self.open_springer()
        results = self.get_search_results()
        self.download_pdfs(results)
        print(results)


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
    "--page",
    default=1,
    help="Page to download",
    prompt="Input page number, default is 1.",
)
@click.option(
    "--discipline",
    default="Environment",
    prompt="Input discipline, default is Environment",
    help="https://link.springer.com/search?date-facet-mode=between&query=recycling&facet-end-year=%7Bend_year%7D&facet-language=%22En%22&facet-start-year=%7Bstart_year%7D",
)
@click.option(
    "--query", default="recycling", help="Query to download", prompt="Insert query"
)
def main(start, end, page, query, discipline):
    bot = Downloader(
        start=start,
        end=end,
        use_chrome=False,
        page=page,
        search_key=query,
        discipline=discipline,
    )
    bot.run()


if __name__ == "__main__":
    main()