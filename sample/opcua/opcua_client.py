import time
from opcua import Client, ua


class PSOWeighbridgeClient:
    def __init__(self, endpoint, namespace_uri="urn:pso:smart-weighbridge",
                 server_object_name="PSO Smart Weighbridge"):
        self.endpoint = endpoint
        self.namespace_uri = namespace_uri
        self.server_object_name = server_object_name
        self.client = Client(endpoint)
        self.idx = None
        self.root = None

    def connect(self):
        self.client.connect()
        self.root = self.client.get_root_node()
        self.idx = self.client.get_namespace_index(self.namespace_uri)
        print(f"Connected to: {self.endpoint}")
        print(f"Namespace index: {self.idx}")

    def disconnect(self):
        self.client.disconnect()
        print("Disconnected")

    def get_tag_node(self, category_name, tag_name):
        """
        Builds browse path like:
        Objects -> PSO Smart Weighbridge -> Entrance_XK3190_DS8 -> gross_weight_WB1
        """
        path = [
            "0:Objects",
            f"{self.idx}:{self.server_object_name}",
            f"{self.idx}:{category_name}",
            f"{self.idx}:{tag_name}",
        ]
        return self.root.get_child(path)

    def read_tag(self, category_name, tag_name):
        old_value = ""
        try:
            node = self.get_tag_node(category_name, tag_name)
            value = node.get_value()
            print(f"READ  {category_name}.{tag_name} = {value}")
            return value
        except ValueError:
            return 0

    def write_tag(self, category_name, tag_name, value, variant_type=None):
        node = self.get_tag_node(category_name, tag_name)

        if variant_type is not None:
            node.set_value(ua.Variant(value, variant_type))
        else:
            node.set_value(value)

        print(f"WROTE {category_name}.{tag_name} = {value}")

    def browse_category(self, category_name):
        category_node = self.root.get_child([
            "0:Objects",
            f"{self.idx}:{self.server_object_name}",
            f"{self.idx}:{category_name}",
        ])

        print(f"\nTags inside {category_name}:")
        children = category_node.get_children()
        for child in children:
            try:
                print(f"  {child.get_browse_name().Name} = {child.get_value()}")
            except Exception:
                print(f"  {child.get_browse_name().Name}")

    def get_node_by_nodeid(self, nodeid_string):
        """
        Example:
        node = client.get_node('ns=2;s=some_string_id')
        or
        node = client.get_node('ns=2;i=1234')
        """
        return self.client.get_node(nodeid_string)