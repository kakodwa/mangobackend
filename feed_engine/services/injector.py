import random


class FeedInjector:

    @staticmethod
    def inject(
        feed,
        products=None,
        events=None,
        shops=None,
        properties=None,
        lodges=None,
    ):
        result = []
        counter = 0

        available_blocks = []

        if products:
            available_blocks.append("products")

        if events:
            available_blocks.append("events")

        if shops:
            available_blocks.append("shops")

        if properties:
            available_blocks.append("properties")

        if lodges:
            available_blocks.append("lodges")

        last_block = None

        for item in feed:
            result.append(item)
            counter += 1

            # inject after every 5 primary items
            if counter % 1 != 0:
                continue

            choices = [
                block
                for block in available_blocks
                if block != last_block
            ]

            if not choices:
                continue

            block_type = random.choice(choices)

            if block_type == "products":
                result.append({
                    "type": "horizontal_products",
                    "data": products[:10]
                })

            elif block_type == "events":
                result.append({
                    "type": "horizontal_events",
                    "data": events[:10]
                })

            elif block_type == "shops":
                result.append({
                    "type": "horizontal_shops",
                    "data": shops[:10]
                })

            elif block_type == "properties":
                result.append({
                    "type": "horizontal_properties",
                    "data": properties[:10]
                })

            elif block_type == "lodges":
                result.append({
                    "type": "horizontal_lodges",
                    "data": lodges[:10]
                })

            last_block = block_type

        return result