import json
import logging
from urllib.parse import urljoin
import urllib.request
import re
from process_time_and_distance_sheet import load_and_transform_provider_time_distance
from process_minimum_provider import get_minimum_provider_sheet_df,get_max_time_and_distance

def load_config():
    with open('./config.json') as config:
        return json.load(config)
    
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def download_file(url):
    config=load_config()
    tag_pattern = re.compile(rf"{config['file_match_pattern']}", re.IGNORECASE)
    with urllib.request.urlopen(url) as response:
        for line in response:
            try:
                line=line.decode('utf-8')
            except UnicodeDecodeError:
                continue

            match=tag_pattern.search(line)
            if match:
                href=match.group(1)
                file_url=urljoin(url,href)
                file_name=file_url.split('/')[-1]
                try:
                    urllib.request.urlretrieve(file_url,file_name)
                    logger.info(f'File downloaded at current directory:{file_name}')
                except Exception as e:
                    logger.info(f"Error downloading file{e}")
                return file_name,file_url            

def main():
    config=load_config()
    file_name,file_url=download_file(config['url'])
    try:
        time_distance_df=load_and_transform_provider_time_distance(file_name,config['sheets']['time_distance'],file_url)
        time_distance_df.to_excel('Time and Distance.xlsx',sheet_name='Provider Time and Distance',index=False)
        print("Minimum Provider Time and Distance sheet created sucessfully")
    except Exception as e:
        print(f'Error{e}')
    try:
        minimum_provider_df=get_max_time_and_distance(time_distance_df,file_name,config['sheets']['minimums'])
        minimum_provider_df.to_excel('Minimums.xlsx',sheet_name='Minimum Provider',index=False)
        print("Minimum Provider Count Sheet created sucessfully")

    except Exception as e:
        print(f'Error:{e}')
if __name__=="__main__":
    main()