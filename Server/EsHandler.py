import json
from prettytable import PrettyTable
from elasticsearch import Elasticsearch


class EsHandler:

    def __init__(self, db_name, es_url):
        self.pt = PrettyTable()
        self.db_name = db_name
        self.es = Elasticsearch(es_url)


    # tabulate es date using prettytable
    def tabulate_data(self, resp):
        for hit in resp:
            self.pt.field_names = ["Client ID", "Mac Address", "IP", "System", "Node Name", "Release", "Version", "Machine", "Date-Joined", "Time-Joined", "User"]
            self.pt.add_row([
                         hit["_id"],

                         hit["_source"].get("mac-address"),
                         hit["_source"].get("ip"),
                         hit["_source"].get("os"),
                         hit["_source"].get("system-name"),
                         hit["_source"].get("release"),
                         hit["_source"].get("version"),
                         hit["_source"].get("machine"),
                         hit["_source"].get("date-joined"),
                         hit["_source"].get("time-joined"),
                         hit["_source"].get("user")
                         ])
        print(self.pt)
        self.pt.clear()


    # saves first portion of client file in index
    def index_client_data(self, client_info):
        try:
            resp = self.es.index(index=self.db_name, document=client_info)
            return resp.get('_id')
        except Exception as e:
            print("[-] Unable to store data!!!")
            print(e)


    # retrieve client information documents from elastic search
    def retrieve_client_information(self):
        try:
            response = self.es.search(index=self.db_name, size=100, query={"match_all": {}})
            self.tabulate_data(response['hits']['hits'])
        except Exception as e:
                print(e)


    # Retrieve client information documents from Elasticsearch by client ID
    def get_client_data(self, client_id):
        try:
            query = {
                "query": {
                    "term": {
                        "_id": client_id  # Match the Elasticsearch document ID
                    }
                }
            }
            response = self.es.search(index=self.db_name, size=1, body=query)
            hits = response['hits']['hits']

            # Return the document if found, otherwise return None
            if hits:
                return {'_id': hits[0]['_id'], '_source': hits[0]['_source']}
            else:
                print(f"[-] No document found with ID: {client_id}")
                return None
        except Exception as e:
            print(f"[-] An error occurred: {e}")
            return None


    # deletes client document from index
    def delete_doc(self, client_id):
        try:
            self.es.delete(index=self.db_name, id=client_id)
            print("[+] Document deleted successfully!!! \n")
        except:
            print("[-] Document does not exist!!! \n")


    # deletes all documents in specified index
    def delete_all_docs(self):
        try:
            self.es.delete_by_query(index=self.db_name, body={"query": {"match_all": {}}})
            print("[+] Documents deleted sucessfully!!!")
        except Exception as e:
            print(e)
            print("[-] Unable delete documents")


    # displays specified feilds in a document
    def show_fields(self, client_id):
        try:
            resp = self.es.get(index=self.db_name, id=client_id)
            self.pt.field_names = ["Client Fields"]

            for field in resp["_source"].keys():
                self.pt.add_row([field])

            print(self.pt)
            self.pt.clear()

        except Exception as e:
            print("[-] Document does not exist!!! /n")


    # retrieves the specified feild in a document
    def get_field(self, client_id: str, feild_parameter):
        try:
            resp = self.es.get(index=self.db_name, id=client_id)
            resp = resp['_source'].get(feild_parameter)

            if resp == "null":
                print("[-]Field does not exist")
            else:
                print(json.dumps(resp, indent=4))
        except:
            print("[-] Field does not exist")


    # Checks if connected client is present in Elasticsearch index by MAC address
    def is_client_present(self, user: str):
        try:
            resp = self.es.search(index=self.db_name, query={"match": {"user": user}})
            if resp['hits']['total']['value'] > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"[-] An error occurred while checking for MAC address: {e}")
            return False


    # updates existing client document using client mac address as identifier
    def update_document(self, client_id: str, client_data):
        try:
            resp = self.es.search(index=self.db_name,  query={"match": {"_id": client_id}})
            for hit in resp['hits']['hits']:
                client_id = (hit["_id"])

            resp = self.es.update(index=self.db_name, id=client_id, doc=client_data)
        except Exception as e:
            print("[-] Document does not exist!!! /n")


    def is_client_connected(self, client_ip: str):
        try:
            resp = self.es.search(index=self.db_name, query={"match": {"ip": client_ip}})
            self.tabulate_data(resp)
        except Exception as e:
            print(f"[-] An error occurred: {e}")


    def get_client_ip(self, client_id: str):
        try:
            resp = self.es.get(index=self.db_name, id=client_id)
            return resp["_source"]["ip"]
        except Exception as e:
            print(f"[-] An error occurred: {e}")



    def get_client_id(self, key: str, value: str):
        try:
            query = {"query": {"match": {key: value}}}
            resp = self.es.search(index=self.db_name, body=query)
            if resp["hits"]["hits"]:
                return resp["hits"]["hits"][0]["_id"]
            return None
        except Exception as e:
            print(f"[-] get_client_id error: {e}")
            return None


    # retrieves document from index
    def retrieve_client_document(self, client_id: str):
        try:
            resp = self.es.get(index=self.db_name, id=client_id)
            print(json.dumps(resp['_source'], indent=4))
            return resp
        except:
            print("[-] Document does not exist!!! /n")
