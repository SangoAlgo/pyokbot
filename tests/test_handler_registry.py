class TestHandlerRegistry:
    def test_register_handler(self, sample_vanus):
        async def dummy(msg):
            pass

        decorator = sample_vanus.on_message(filters="user")
        decorator(dummy)

        assert len(sample_vanus.ws.handles_list) == 1
        handler = sample_vanus.ws.handles_list[0]
        assert handler["func"] == dummy
        assert handler["filters"]["filters"] == "user"

    def test_register_command_handler(self, sample_vanus):
        async def cmd_start(msg):
            pass

        decorator = sample_vanus.on_message(commands=["start"])
        decorator(cmd_start)

        handler = sample_vanus.ws.handles_list[-1]
        assert handler["func"] == cmd_start
        assert handler["filters"]["commands"] == ["start"]

    def test_register_content_type_handler(self, sample_vanus):
        async def handle_photo(msg):
            pass

        decorator = sample_vanus.on_message(content_types=["photo"])
        decorator(handle_photo)

        handler = sample_vanus.ws.handles_list[-1]
        assert handler["filters"]["content_types"] == ["photo"]

    def test_register_text_handler(self, sample_vanus):
        async def handle_text(msg):
            pass

        decorator = sample_vanus.on_message(text="hello")
        decorator(handle_text)

        handler = sample_vanus.ws.handles_list[-1]
        assert handler["filters"]["text"] == "hello"

    def test_register_multiple_handlers_order(self, sample_vanus):
        async def h1(msg):
            pass

        async def h2(msg):
            pass

        async def h3(msg):
            pass

        sample_vanus.on_message(commands=["start"])(h1)
        sample_vanus.on_message(commands=["help"])(h2)
        sample_vanus.on_message(filters="user")(h3)

        assert len(sample_vanus.ws.handles_list) == 3
        assert sample_vanus.ws.handles_list[0]["func"] == h1
        assert sample_vanus.ws.handles_list[1]["func"] == h2
        assert sample_vanus.ws.handles_list[2]["func"] == h3
