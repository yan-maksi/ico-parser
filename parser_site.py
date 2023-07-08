import csv
import json
from typing import List
from bs4 import BeautifulSoup
import requests
import pandas as pd
from selenium import webdriver
from time import sleep


def write_to_csv(data: List, directory: str):
    """
    Write file to CSV format

    Args:
        data: list of data to upload
        directory: path to CSV file

    Returns: None
        SCV file to directory
    """
    try:
        with open(directory, "a") as fopen:
            csv_writer = csv.writer(fopen)
            csv_writer.writerow(data)
    finally:
        return "Error when you try write data"


def scrape_page(url: str):
    """
    Open necessary page

    Args:
        url: url to open

    Returns:
        parsed url
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    # opening up connection, scrapping the page
    response = requests.get(url, headers=headers)
    html_content = response.text
    # html parsing
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup, response


def key_includes_number(json_obj):
    for key in json_obj.keys():
        if any(char.isdigit() for char in key):
            return True
    return False


def delete_key_with_number(json_obj):
    keys_to_delete = []
    for key, value in json_obj.items():
        if key_contains_number(key) or value is None:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        del json_obj[key]


def key_contains_number(key):
    return any(char.isdigit() for char in key)


def scrape(url):
    # Instantiate a Selenium WebDriver
    driver = webdriver.Chrome()
    driver.get(url)

    full_data_about_coin = []
    try:
        # Simulate scrolling to load dynamic content
        for i in range(14):  # The number of times of scrolls 16
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)  # Add a delay to allow content to load (adjust as needed)

            # Retrieve the updated HTML content
            html_content = driver.page_source

            # Create a BeautifulSoup object using the updated HTML content
            coin_html_content = BeautifulSoup(html_content, 'html.parser')
            containers = coin_html_content.findAll("div", {"class": "white-desk ico-card"})
            print(f'len of conteiner {len(containers)} in {i} iteration')

            # take the data we need from all ico
            for coin in containers:
                try:
                    interest = coin.find("div", class_="nr").text
                except AttributeError:
                    interest = coin.find("div", class_="all_site_val").text


                category = coin.find("div", class_="categ_type").text
                try:
                    received_money = coin.find("div", id="new_column_categ_invisted").text.replace('\n', '')
                except AttributeError:
                    received_money = coin.find("span", id="notset").text

                try:
                    goal = coin.find("span", class_="notset").text
                except AttributeError:
                    goal = coin.find("div", id="categ_desctop").find("span").text

                end_date = coin.find("div", class_="date").text.replace('\n', '')

                coin_ticker = coin.find("div", class_="ico-main-info").find("h3").text.replace("\n", "")

                link_to_coin_page = coin.find("div", class_="ico-main-info").contents[1].contents[0].attrs['href']
                # print(f'Link to coin page: {link_to_coin_page}')

                # parse coin page
                soup_content, response = scrape_page(link_to_coin_page)
                if response.status_code != 403:
                    soup = soup_content.findAll("div", {"class": "col-12 col-lg-10"})[0]

                    sold_coins = soup.find('div', {'class': 'goal'}).contents
                    if len(sold_coins) < 2:
                        sold_coins = None
                    else:
                        sold_coins = sold_coins[2]

                    # get start and end date coin sell
                    start_end_date_coin_sell = soup.find('div', {'class': 'col-12 title-h4'}).contents[3].text.replace('\n', '').replace(
                        'Token Sale:', '').replace('Token Sale:', '')

                    # get all data about current coin
                    row_list_data = soup.find("div", class_="row list").findAll('span')

                    coin_data_dict: dict = {}
                    for data in row_list_data:
                        try:
                            if data.next == 'Ticker: ':
                                continue
                            else:
                                coin_data_dict[data.next.replace(':', "")] = data.nextSibling

                        except Exception as e:
                            print(f'Error when try to parse coin data: {e}')
                            pass

                    try:
                        role_of_token = soup.find("div", class_="col-12 info-analysis-list").findAll('span')[0].nextSibling
                    except Exception as e:
                        print(f'Error when try to parse coin data: {e}')
                        pass

                    main_page_data = {"interest": interest, "category": category, "received_money": received_money,
                                       "goal": goal, "end_date": end_date, "coin_ticker": coin_ticker,
                                       "sold_coins": sold_coins,
                                       "start_end_date_coin_sell": start_end_date_coin_sell,
                                       "role_of_token": role_of_token}

                    # add data from data coin page to main page
                    main_page_data.update(coin_data_dict)
                    # print(main_page_data)
                    full_data_about_coin.append(main_page_data)

    except Exception as e:
        print(f'Error: {e}')
        pass

    # Extract unique keys from the JSON data
    print(f'Len of full_data_about_coin afret: {len(full_data_about_coin)}')
    all_keys = set()
    for obj in full_data_about_coin:
        if key_includes_number(obj):
            delete_column_with_number = delete_key_with_number(obj)
            try:
                all_keys.update(delete_column_with_number)
            except Exception as e:
                pass
        else:
            all_keys.update(obj.keys())

    print(all_keys)
    # Create an empty DataFrame with the extracted keys as column names
    df = pd.DataFrame(columns=sorted(all_keys))

    # Iterate over the JSON objects and populate the DataFrame
    for obj in full_data_about_coin:
        row = {key: obj.get(key) for key in all_keys}
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    # Write the DataFrame to a CSV file
    df.to_csv('ico.csv', index=False)


if __name__ == "__main__":
    # define the URL that we will get the data from and call the function
    my_url = 'https://icodrops.com/category/ended-ico/'
    scrape(my_url)
    print(f'{my_url} - scraped')
    print("Successfully scraped all pages!")
