from __future__ import annotations

namespace_script = """
namespace eval ttk::theme::{theme_name} {{
    package provide ttk::theme::{theme_name} 1.0

    ttk::style theme create {theme_name} -parent {parent_theme} -settings {{
        proc load_images {{}} {{
            variable images
            foreach file [glob -directory {path} *.png] {{
                set images([file tail [file rootname $file]]) [image create photo -file $file -format png]
            }}
        }}
        load_images
        {theme_body}
    }}
}}
"""


class MainNamespace:
    @staticmethod
    def generate(theme_name, parent_theme, img_res_path, theme_body):
        return namespace_script.format(
            theme_name=theme_name,
            parent_theme=parent_theme,
            path=img_res_path,
            theme_body=theme_body,
        )


class Element:
    class_name: str
    state_order = ["{selected disabled}", "disabled", "selected", "pressed", "active"]
    style_map = "ttk::style map {class_name} -foreground [list {colors}]"
    style_config = "ttk::style configure {class_name} {kwargs}"
    style_element = (
        "ttk::style element create {element} image [list {image_list}] -border 4 -sticky nsew"
    )

    @classmethod
    def generate(cls, **kwargs):
        return cls.settings.format(
            map=cls.generate_style_map(kwargs),
            configure=cls.generate_style_configure(kwargs),
            element=cls.generate_style_element(kwargs),
        )

    @classmethod
    def generate_style_map(cls, kwargs):
        result = []
        for key, value in kwargs.items():
            if "color" in value:
                if ":" in key:
                    key = "{" + " ".join(key.split(":")) + "}"
                if "hover" in key:
                    key = key.replace("hover", "active")
                result.append(key)
                result.append(value["color"])

        return cls.style_map.format(class_name=cls.class_name, colors=" ".join(result))

    @classmethod
    def generate_style_configure(cls, kwargs):
        rest_props = kwargs["rest"]
        args = ""
        if "padding" in rest_props:
            args += f"-padding {{{rest_props['padding'].replace('px', '')}}}"
        if "anchor" in rest_props:
            args += f" -anchor {rest_props['anchor']}"
        if "color" in rest_props:
            args += f" -foreground {rest_props['color']}"

        return cls.style_config.format(class_name=cls.class_name, kwargs=args)

    @classmethod
    def generate_style_element(cls, kwargs):
        result = []
        get_image = lambda image: f"$images({image.replace('$', '')})"

        for key, value in kwargs.items():
            if key == "rest" or "image" not in value:
                continue

            if ":" in key:
                key = "{" + " ".join(key.split(":")) + "}"
            if "hover" in key:
                key = key.replace("hover", "active")

            result.append((key, get_image(value["image"])))

        result.sort(key=lambda e: cls.state_order.index(e[0]))

        sorted_result = [get_image(kwargs["rest"]["image"])]
        for key_value_pair in result:
            sorted_result.extend(key_value_pair)

        return cls.style_element.format(element=cls.main_element, image_list=" ".join(sorted_result))


class Button(Element):
    class_name = "TButton"
    main_element = "Button.button"
    settings = """
        ttk::style layout TButton {{
            Button.button -children {{
                Button.padding -children {{
                    Button.focus -children {{
                        Button.label -side left -expand 1
                    }}
                }}
            }}
        }}
        {configure}
        {map}
        {element}
    """
