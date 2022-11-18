from urllib import response
import scrapy
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class SohoaVnexpressNet(scrapy.Spider):
    name = "sohoa"
    SearchTagPerPage = 100
    MaxRetryNum = 10
    base_url='https://stackoverflow.com'
    host ='https://ithelper.cafesua.net'
    auth_token='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2l0aGVscGVyLmNhZmVzdWEubmV0IiwiaWF0IjoxNjY4NDc2MDk5LCJuYmYiOjE2Njg0NzYwOTksImV4cCI6MTY2OTA4MDg5OSwiZGF0YSI6eyJ1c2VyIjp7ImlkIjoiMSJ9fX0.JzGEnv-uJTWnMw7T_C2IJ5YDut1fR7GkGpoN0Aga4Kw'
    authorization = "Bearer " + auth_token # 'Bearer xxx'
    requestsProxies = requestsProxies=None
    requestsProxies = requestsProxies
    # requests.adapters.DEFAULT_RETRIES = 10
    reqSession = requests.Session()
    reqRetry = Retry(connect=MaxRetryNum, backoff_factor=0.5)
    reqAdapter = HTTPAdapter(max_retries=reqRetry)
    reqSession.mount('http://', reqAdapter)
    reqSession.mount('https://', reqAdapter)
    apiTags = host + "/wp-json/wp/v2/tags" # 'https://www.crifan.org/wp-json/wp/v2/tags'
    apiCategories = host + "/wp-json/wp/v2/categories" 
    def start_requests(self):
        urls=[]
        for i in range(73,90):
            urls.append('https://stackoverflow.com/questions/tagged/python?tab=votes&page={}&pagesize=50'.format(i))
        # urls = [
        #     'https://stackoverflow.com/questions/tagged/python?tab=votes&page=23&pagesize=50',
        # ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_list)

    def parse_list(self, response):
        for question in response.xpath('//*[@id="questions"]/div/div[2]/h3/a/@href').extract():
            yield scrapy.Request(url=self.base_url+question, callback=self.parse_question)

    def parse_question(self,response):
        post={}
        tags=[]
        post['title']=response.xpath('//*[@id="question-header"]/h1/a/text()').extract()[0]
        if self.check_post_exist(post['title']):
            for tag in response.xpath('//*[@id="question"]/div[2]/div[2]/div[2]/div/div/ul/li/a/text()').extract():
                tags.append(tag)
            # print(tags)
                
            question=response.xpath('//*[@id="question"]/div[2]/div[2]/div[1]').extract()[0]
            answer=response.xpath('//*[@id="answers"]/div[contains(@itemprop, "acceptedAnswer")]/div[1]/div[2]/div[1]').extract()[0]
            content='<h2>Question</h2></br> '+question +'</br><h2>Best Solution :</h2></br> '+answer
            # print(answer)
            self.create_wordpress_post(post['title'],content,tags)

    def check_post_exist(self,searchTerm):
        url = "https://ithelper.cafesua.net/wp-json/wp/v2/posts"

        payload={
                'search':searchTerm,
        }
        userAgent = "Mozilla/5.0 ABCD"
        headers = {
        'User-Agent': userAgent,
        }
        response = requests.request("GET", url, headers=headers, params=payload)
        if response.text=='[]':
            return True
        else:
            return False
    def getTaxonomySinglePage(self, name, taxonomy, curPage, perPage=None):
        """Get single page wordpress category/post_tag
            return the whole page items
            by call REST api: 
                GET /wp-json/wp/v2/categories
                GET /wp-json/wp/v2/tags
        Args:
            name (str): category name
            taxonomy (str): taxonomy type: category/post_tag
            curPage (int): current page number
            perPage (int): max items per page. Default None. If None, use SearchTagPerPage=100
        Returns:
            (bool, dict)
                True, found taxonomy info
                False, error detail
        Raises:
        """
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        curHeaders = {
        
            'Authorization': 'Bearer '+self.auth_token,
            'User-Agent': userAgent,
  
        }
        logging.debug("curHeaders=%s", curHeaders)

        if perPage is None:
            perPage = self.SearchTagPerPage

        queryParamDict = {
            "search": name, # 'Mac'
            "page": curPage, # 1
            "per_page": perPage, # 100
        }

        searchTaxonomyUrl = ""
        if taxonomy == "category":
            searchTaxonomyUrl = self.apiCategories
        elif taxonomy == "post_tag":
            searchTaxonomyUrl = self.apiTags

        # resp = requests.get(
        resp = self.reqSession.get(
            searchTaxonomyUrl,
            # proxies=self.requestsProxies,
            headers=curHeaders,
            # data=queryDict, # {'search': 'Mac'}
            params=queryParamDict, # {'search': 'Mac'}
        )
        logging.debug("resp=%s for GET %s with para=%s", resp, searchTaxonomyUrl, queryParamDict)

        isSearchOk, respTaxonomyLit = self.processCommonResponse(resp)
        logging.debug("isSearchOk=%s, respTaxonomyLit=%s", isSearchOk, respTaxonomyLit)

        return isSearchOk, respTaxonomyLit
    @staticmethod           
    def findSameNameTaxonomy(name, taxonomyLit):
        """Search same taxonomy (category/tag) name from taxonomy (category/tag) list
        Args:
            name (str): category/tag name to find
            taxonomyLit (list): category/tag list
        Returns:
            found taxonomy info (dict)
        Raises:
        """
        foundTaxonomy = None

        sameNameTaxonomy = None
        lowercaseSameNameTaxonomy = None
        lowerName = name.lower() # 'mac'

        for eachTaxonomy in taxonomyLit:
            curTaxonomyName = eachTaxonomy["name"] # 'Cocoa', 'Mac'
            curTaxonomyLowerName = curTaxonomyName.lower() # 'cocoa', 'mac'
            if curTaxonomyName == name:
                sameNameTaxonomy = eachTaxonomy
                break
            elif curTaxonomyLowerName == lowerName:
                lowercaseSameNameTaxonomy = eachTaxonomy

        if sameNameTaxonomy:
            foundTaxonomy = sameNameTaxonomy
        elif lowercaseSameNameTaxonomy:
            foundTaxonomy = lowercaseSameNameTaxonomy

        return foundTaxonomy 
    def getAllTaxonomy(self, name, taxonomy):
        """Get all page of wordpress category/post_tag
        Args:
            name (str): category name to search
            taxonomy (str): taxonomy type: category/post_tag
        Returns:
            (bool, dict)
                True, found taxonomy info
                False, error detail
        Raises:
        """
        isGetAllOk = False
        respInfo = None

        perPage = self.SearchTagPerPage

        firstPageNum = 1
        isFirstPageSearchOk, firstPageRespInfo = self.getTaxonomySinglePage(name, taxonomy, firstPageNum, perPage)
        if isFirstPageSearchOk:
            isGetAllOk = True

            firstPageRespList = firstPageRespInfo
            respAllTaxonomyLit = firstPageRespList
            firstPageRespItemNum = len(firstPageRespList)
            if firstPageRespItemNum >= perPage:
                # get next page
                isRestEachPageOk = True
                isRestEachPageRespFull = True
                restCurPage = firstPageNum + 1
                restRespAllItemList = []
                while (isRestEachPageOk and isRestEachPageRespFull):
                    isRestEachPageOk, restEachPageRespItemList = self.getTaxonomySinglePage(name, taxonomy, restCurPage, perPage)
                    if isRestEachPageOk:
                        restEachPageRespItemNum = len(restEachPageRespItemList)
                        isRestEachPageRespFull = restEachPageRespItemNum >= perPage

                        restRespAllItemList.extend(restEachPageRespItemList)

                    restCurPage += 1

                respAllTaxonomyLit.extend(restRespAllItemList)

            respInfo = respAllTaxonomyLit
        else:
            isGetAllOk = False
            respInfo = firstPageRespInfo

        return isGetAllOk, respInfo           
    def searchTaxonomy(self, name, taxonomy):
        """Search wordpress category/post_tag
            return the exactly matched one, name is same, or name lowercase is same
        Args:
            name (str): category name to search
            taxonomy (str): taxonomy type: category/post_tag
        Returns:
            (bool, dict)
                True, found taxonomy info
                False, error detail
        Raises:
        """
        isSearchOk = False
        finalRespTaxonomy = None

        isGetAllOk, respInfo = self.getAllTaxonomy(name, taxonomy)
        if isGetAllOk:
            isSearchOk = True
            respAllTaxonomyLit = respInfo
            finalRespTaxonomy = self.findSameNameTaxonomy(name, respAllTaxonomyLit)
            logging.debug("finalRespTaxonomy=%s", finalRespTaxonomy)

        return isSearchOk, finalRespTaxonomy
    def createTaxonomy(self, name, taxonomy, parent=None, slug=None, description=None):
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        curHeaders = {       
            'Authorization': 'Bearer '+self.auth_token,
            'User-Agent': userAgent,
        }
        logging.debug("curHeaders=%s", curHeaders)

        postDict = {
            "name": name, #
        }
        if slug:
            postDict["slug"] = slug

        if description:
            postDict["description"] = description

        if taxonomy == "category":
            if parent:
                postDict["parent"] = parent

        createTaxonomyUrl = ""
        if taxonomy == "category":
            createTaxonomyUrl = self.apiCategories
        elif taxonomy == "post_tag":
            createTaxonomyUrl = self.apiTags

        # resp = requests.post(
        resp = requests.post(
            createTaxonomyUrl,
            # proxies=self.requestsProxies,
            headers=curHeaders,
            json=postDict,
        )
        logging.info("resp=%s for POST %s with postDict=%s", resp, createTaxonomyUrl, postDict)
        isCreateOk, respInfo = self.processCommonResponse(resp)
        logging.debug("isCreateOk=%s, respInfo=%s", isCreateOk, respInfo)


        return isCreateOk, respInfo
    @staticmethod    
    def processCommonResponse(resp):
        isOk, respInfo = False, {}

        if resp.ok:
            respJson = resp.json()
            # logging.debug("respJson=%s", respJson)
            if isinstance(respJson, dict):
                isOk = True

                if "id" in respJson:
                    newId = respJson["id"]
                    newSlug = respJson["slug"]
                    newLink = respJson["link"]
                    logging.debug("newId=%s, newSlug=%s, newLink=%s", newId, newSlug, newLink) # newId=13224, newSlug=gpu, newLink=https://www.crifan.org/tag/gpu/
                    respInfo = {
                        "id": newId, # 70393
                        "slug": newSlug, # f6956c30ef0b475fa2b99c2f49622e35
                        "link": newLink, # https://www.crifan.org/f6956c30ef0b475fa2b99c2f49622e35/
                    }

                    if "type" in respJson:
                        curType = respJson["type"]
                        if (curType == "attachment") or (curType == "post"):
                            respInfo["url"] = respJson["guid"]["rendered"]
                            # "url": newUrl, # https://www.crifan.org/files/pic/uploads/2020/03/f6956c30ef0b475fa2b99c2f49622e35.png
                            respInfo["title"] = respJson["title"]["rendered"]
                            # "title": newTitle, # f6956c30ef0b475fa2b99c2f49622e35
                            logging.debug("url=%s, title=%s", respInfo["url"], respInfo["title"])

                    if "taxonomy" in respJson:
                        curTaxonomy = respJson["taxonomy"]
                        # common for category/post_tag
                        respInfo["name"] = respJson["name"]
                        respInfo["description"] = respJson["description"]
                        logging.debug("name=%s, description=%s", respInfo["name"], respInfo["description"])

                        if curTaxonomy == "category":
                            respInfo["parent"] = respJson["parent"]
                            logging.debug("parent=%s", respInfo["parent"])
                else:
                    respInfo = respJson

                logging.debug("respInfo=%s", respInfo)
            elif isinstance(respJson, list):
                isOk = True
                respInfo = respJson
        else:
            # error example:
            # resp=<Response [403]> for GET https://www.crifan.org/wp-json/wp/v2/categories with para={'search': '印象笔记'}
            # ->
            # {'errCode': 403, 'errMsg': '{"code":"jwt_auth_invalid_token","message":"Expired token","data":{"status":403}}'}
            isOk = False
            # respInfo = resp.status_code, resp.text
            respInfo = {
                "errCode": resp.status_code,
                "errMsg": resp.text,
            }

        logging.debug("isOk=%s, respInfo=%s", isOk, respInfo)
        return isOk, respInfo                    
    def getTaxonomyIdList(self, nameList, taxonomy):
        """convert taxonomy(category/post_tag) name list to wordpress category/post_tag id list
        Args:
            nameList (list): category/post_tag name list
            taxonomy (str): the name type: category/post_tag
        Returns:
            taxonomy id list(list)
        Raises:
        """
        taxonomyIdList = []

        totalNum = len(nameList)
        for curIdx, eachTaxonomyName in enumerate(nameList):
            curNum = curIdx + 1
            logging.info("%s taxonomy [%d/%d] %s %s", "-"*10, curNum, totalNum, eachTaxonomyName, "-"*10)
            curTaxonomy = None

            isSearhOk, existedTaxonomy = self.searchTaxonomy(eachTaxonomyName, taxonomy)
            logging.debug("isSearhOk=%s, existedTaxonomy=%s", isSearhOk, existedTaxonomy)
            # isSearhOk=True, existedTaxonomy={'id': 1374, 'count': 350, 'description': '', 'link': 'https://www.crifan.org/category/work_and_job/operating_system_and_platform/mac/', 'name': 'Mac', 'slug': 'mac', 'taxonomy': 'category', 'parent': 4624, 'meta': [], '_links': {'self': [{'href': 'https://www.crifan.org/wp-json/wp/v2/categories/1374'}], 'collection': [{'href': 'https://www.crifan.org/wp-json/wp/v2/categories'}], 'about': [{'href': 'https://www.crifan.org/wp-json/wp/v2/taxonomies/category'}], 'up': [{'embeddable': True, 'href': 'https://www.crifan.org/wp-json/wp/v2/categories/4624'}], 'wp:post_type': [{'href': 'https://www.crifan.org/wp-json/wp/v2/posts?categories=1374'}], 'curies': [{'name': 'wp', 'href': 'https://api.w.org/{rel}', 'templated': True}]}}
            if isSearhOk and existedTaxonomy:
                curTaxonomy = existedTaxonomy
                logging.info("Found existed %s: name=%s,id=%s,slug=%s", taxonomy, curTaxonomy["name"], curTaxonomy["id"], curTaxonomy["slug"])
            else:
                isCreateOk, createdTaxonomy = self.createTaxonomy(eachTaxonomyName, taxonomy)
                logging.debug("isCreateOk=%s, createdTaxonomy=%s", isCreateOk, createdTaxonomy)
                if isCreateOk and createdTaxonomy:
                    curTaxonomy = createdTaxonomy
                    logging.info("New created %s: name=%s,id=%s,slug=%s", taxonomy, curTaxonomy["name"], curTaxonomy["id"], curTaxonomy["slug"])
                else:
                    logging.error("Fail to create %s %s", taxonomy, eachTaxonomyName)

            if curTaxonomy:
                curTaxonomyId = curTaxonomy["id"]
                logging.debug("curTaxonomyId=%s", curTaxonomyId)
                taxonomyIdList.append(curTaxonomyId)
            else:
                logging.error("Fail search or create for %s: %s", taxonomy, eachTaxonomyName)

        logging.info("%s nameList=%s -> taxonomyIdList=%s", taxonomy, nameList, taxonomyIdList)
        return taxonomyIdList
    def create_wordpress_post(self,title,content,tagNameList=[]):
        if tagNameList:
            # ['切换', 'GPU', 'pmset', '显卡模式']
            tagIdList = self.getTaxonomyIdList(tagNameList, taxonomy="post_tag")
            # post_tag nameList=['切换', 'GPU', 'pmset', '显卡模式'] -> taxonomyIdList=[1367, 13224, 13225, 13226]
        url = "https://ithelper.cafesua.net/wp-json/wp/v2/posts"

        payload={
                'title':title,
                'content':content,
                'status':'publish',
                "tags": tagIdList,
        }
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        headers = {
        'Authorization': 'Bearer '+self.auth_token,
        'User-Agent': userAgent,
        }
        response = requests.request("POST", url, headers=headers, json=payload)
        print(response.status_code)