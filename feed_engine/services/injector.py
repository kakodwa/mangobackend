import random


class FeedInjector:

    @staticmethod
    def horizontal_item(
        item_type,
        title,
        view_all_type,
        data,
    ):
        return {
            "type": item_type,
            "title": title,
            "view_all_type": view_all_type,
            "data": data[:10],
        }

    @staticmethod
    def inject(
        items_list,
        injection_interval=12,  # Change to 12 or 18 based on preference
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

        for item in items_list:
            result.append(item)
            counter += 1

            # Inject after reaching the specified single item count
            if counter % injection_interval != 0:
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
                result.append(
                    FeedInjector.horizontal_item(
                        "horizontal_products",
                        "Trending Products",
                        "product",
                        products,
                    )
                )

            elif block_type == "events":
                result.append(
                    FeedInjector.horizontal_item(
                        "horizontal_events",
                        "Upcoming Events",
                        "event",
                        events,
                    )
                )

            elif block_type == "shops":
                result.append(
                    FeedInjector.horizontal_item(
                        "horizontal_shops",
                        "Featured Shops",
                        "shop",
                        shops,
                    )
                )

            elif block_type == "properties":
                result.append(
                    FeedInjector.horizontal_item(
                        "horizontal_properties",
                        "Featured Properties",
                        "property",
                        properties,
                    )
                )

            elif block_type == "lodges":
                result.append(
                    FeedInjector.horizontal_item(
                        "horizontal_lodges",
                        "Recommended Lodges",
                        "lodge",
                        lodges,
                    )
                )

            last_block = block_type

        return result