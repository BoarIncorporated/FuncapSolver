import base64
import json
import time
import random
from typing import Any, Dict

from . import arkose, constants, hash, models, utils

PARAMS = constants.TIMEZONE_API_PARAMS


def get_bda(
    fp: Dict[str, Any],
    preset: models.Preset,
    user_agent: str,
    capi_version: str,
    enforcement_hash: str,
    proxy: str,
) -> str:
    fingerprint = models.Fingerprint.from_raw_data(fp)

    t0 = time.time()
    fe = fingerprint.fe

    try:
        ipdata = utils.fetch_ip_data(proxy)

    except:
        ipdata = models.IPData(timezone_offset=-60, language="en-US", languages="en-US,en")

    for i, entry in enumerate(fe):
            if entry.startswith("TO:"):
                fe[i] = f"TO:{ipdata.timezone_offset}"
                break

    enhanced_fp = [
        {
            "key": "webgl_extensions",
            "value": fingerprint.webgl.get("webgl_extensions", "ANGLE_instanced_arrays;EXT_blend_minmax;EXT_color_buffer_half_float;EXT_shader_texture_lod;EXT_texture_filter_anisotropic;EXT_sRGB;OES_element_index_uint;OES_fbo_render_mipmap;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_color_buffer_float;WEBGL_compressed_texture_astc;WEBGL_compressed_texture_etc;WEBGL_compressed_texture_etc1;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBGL_lose_context;WEBGL_multi_draw"),
        },
        {
            "key": "webgl_extensions_hash",
            "value": fingerprint.webgl.get("webgl_extensions_hash", "3c34b0dc0e73d2c83a91218a631a242d"),
        },
        {"key": "webgl_renderer", "value": fingerprint.webgl.get("webgl_renderer", "WebKit WebGL")},
        {"key": "webgl_vendor", "value": fingerprint.webgl.get("webgl_vendor", "WebKit")},
        {"key": "webgl_version", "value": fingerprint.webgl.get("webgl_version", "WebGL 1.0 (OpenGL ES 2.0 Chromium)")},
        {
            "key": "webgl_shading_language_version",
            "value": fingerprint.webgl.get("webgl_shading_language_version", "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)"),
        },
        {
            "key": "webgl_aliased_line_width_range",
            "value": fingerprint.webgl.get("webgl_aliased_line_width_range", "[1, 10]"),
        },
        {
            "key": "webgl_aliased_point_size_range",
            "value": fingerprint.webgl.get("webgl_aliased_point_size_range", "[1, 2047]"),
        },
        {
            "key": "webgl_antialiasing",
            "value": fingerprint.webgl.get("webgl_antialiasing", "yes"),
        },
        {"key": "webgl_bits", "value": fingerprint.webgl.get("webgl_bits", "8,8,24,8,8,0")},
        {
            "key": "webgl_max_params",
            "value": fingerprint.webgl.get("webgl_max_params", "16,192,4096,1024,32768,32,4096,31,16,32,1024"),
        },
        {
            "key": "webgl_max_viewport_dims",
            "value": fingerprint.webgl.get("webgl_max_viewport_dims", "[32768, 32768]"),
        },
        {
            "key": "webgl_unmasked_vendor",
            "value": fingerprint.webgl.get("webgl_unmasked_vendor", "Qualcomm"),
        },
        {
            "key": "webgl_unmasked_renderer",
            "value": fingerprint.webgl.get("webgl_unmasked_renderer", "Adreno (TM) 640"),
        },
        {"key": "webgl_vsf_params", "value": fingerprint.webgl.get("webgl_vsf_params", "23,127,127,10,15,15,10,15,15")},
        {"key": "webgl_vsi_params", "value": fingerprint.webgl.get("webgl_vsi_params", "0,31,30,0,31,30,0,31,30")},
        {"key": "webgl_fsf_params", "value": fingerprint.webgl.get("webgl_fsf_params", "23,127,127,10,15,15,10,15,15")},
        {"key": "webgl_fsi_params", "value": fingerprint.webgl.get("webgl_fsi_params", "0,31,30,0,31,30,0,31,30")},
    ]

    enhanced_fp.append(
        {
            "key": "webgl_hash_webgl",
            "value": hash.x64hash128(utils.hashable_webgl(enhanced_fp)),
        }
    )

    enhanced_fp_more = [
        {
            "key": "user_agent_data_brands",
            "value": fingerprint.webgl.get("user_agent_data_brands", "Not A(Brand,Chromium,Google Chrome"),
        },
        {
            "key": "user_agent_data_mobile",
            "value": fingerprint.webgl.get("user_agent_data_mobile", False),
        },
        {
            "key": "navigator_connection_downlink",
            "value": int(fingerprint.webgl.get("navigator_connection_downlink", "10")),
        },  # type:ignore
        {
            "key": "navigator_connection_downlink_max",
            "value": int(
                fingerprint.webgl.get("navigator_connection_downlink_max", -1)
            ),
        },
        {"key": "network_info_rtt", "value": fingerprint.webgl.get("network_info_rtt", 100)},
        {
            "key": "network_info_save_data",
            "value": fingerprint.webgl.get("network_info_save_data", False),
        },
        {
            "key": "network_info_rtt_type",
            "value": fingerprint.webgl.get("network_info_rtt_type", "wifi"),
        },
        {
            "key": "screen_pixel_depth",
            "value": fingerprint.webgl.get("screen_pixel_depth", "24"),
        },
        {
            "key": "navigator_device_memory",
            "value": fingerprint.webgl.get("navigator_device_memory", "4"),
        },
        {
            "key": "navigator_pdf_viewer_enabled",
            "value": fingerprint.webgl.get("navigator_pdf_viewer_enabled", False),
        },
        {
            "key": "navigator_languages",
            "value": ipdata.languages,#fingerprint.webgl.get("navigator_languages", "en-GB,en-US"),
        },
        {
            "key": "window_inner_width",
            "value": fingerprint.webgl.get("window_inner_width", "0"),
        },
        {
            "key": "window_inner_height",
            "value": fingerprint.webgl.get("window_inner_height", "0"),
        },
        {
            "key": "window_outer_width",
            "value": fingerprint.webgl.get("window_outer_width", "1067"),
        },
        {
            "key": "window_outer_height",
            "value": fingerprint.webgl.get("window_outer_height", "480"),
        },
        {
            "key": "browser_detection_firefox",
            "value": fingerprint.webgl.get("browser_detection_firefox", False),
        },
        {
            "key": "browser_detection_brave",
            "value": fingerprint.webgl.get("browser_detection_brave", False),
        },
        {
            "key": "browser_api_checks",
            "value": fingerprint.webgl.get("browser_api_checks", [
                    "permission_status: true",
                    "eye_dropper: false",
                    "audio_data: true",
                    "writable_stream: true",
                    "css_style_rule: true",
                    "navigator_ua: true",
                    "barcode_detector: true",
                    "display_names: true",
                    "contacts_manager: false",
                    "svg_discard_element: false",
                    "usb: defined",
                    "media_device: defined",
                    "playback_quality: true"
                ]),
        },
        {
            "key": "browser_object_checks",
            "value": fingerprint.webgl.get("browser_object_checks"),
        },
        {"key": "29s83ih9", "value": hash.md5hash("false") + "⁣"}, 
        {
            "key": "audio_codecs",
            "value": fingerprint.webgl.get("audio_codecs"),
        },
        {
            "key": "audio_codecs_extended_hash",
            "value": fingerprint.webgl.get("audio_codecs_extended_hash"),
        },
        {
            "key": "video_codecs",
            "value": fingerprint.webgl.get("video_codecs"),
        },
        {
            "key": "video_codecs_extended_hash",
            "value": fingerprint.webgl.get("video_codecs_extended_hash"),
        },
        {
            "key": "media_query_dark_mode",
            "value": fingerprint.webgl.get("media_query_dark_mode", False),
        },
        {
            "key": "css_media_queries",
            "value": fingerprint.webgl.get("css_media_queries", "0"),
        },
        {"key": "css_color_gamut", "value": fingerprint.webgl.get("css_color_gamut", "srgb")},
        {"key": "css_contrast", "value": fingerprint.webgl.get("css_contrast", "no-preference")},
        {"key": "css_monochrome", "value": fingerprint.webgl.get("css_monochrome", False)},
        {"key": "css_pointer", "value": fingerprint.webgl.get("css_pointer", "coarse")},
        {"key": "css_grid_support", "value": fingerprint.webgl.get("css_grid_support", False)},
        {"key": "headless_browser_phantom", "value": False},
        {"key": "headless_browser_selenium", "value": False},
        {"key": "headless_browser_nightmare_js", "value": False},
        {"key": "headless_browser_generic", "value": 4},
        {"key": "1l2l5234ar2", "value": str(int(t0 * 1000))+ "⁣"},
        {"key": "document__referrer", "value": preset.site_url.rstrip("/")},# + "/"},
        {
            "key": "window__ancestor_origins",
            "value": preset.data.window__ancestor_origins,
        },
        {"key": "window__tree_index", "value": preset.data.window__tree_index},
        {"key": "window__tree_structure", "value": preset.data.window__tree_structure},
        {
            "key": "window__location_href",
            "value": f"{preset.api_url}/v2/{capi_version}/enforcement.{enforcement_hash}.html",
        },
        {
            "key": "client_config__sitedata_location_href",
            "value": preset.data.client_config__sitedata_location_href,
        },
        {"key": "client_config__language", "value": None}, #"en",
        {"key": "client_config__surl", "value": preset.api_url},
        {"key": "c8480e29a", "value": hash.md5hash(preset.api_url) + "⁢"},
        {"key": "client_config__triggered_inline", "value": False},
        {"key": "mobile_sdk__is_sdk", "value": False},
        {
            "key": "audio_fingerprint",
            "value": fingerprint.webgl.get("audio_fingerprint"),
        },
        {
            "key": "navigator_battery_charging",
            "value": fingerprint.webgl.get("navigator_battery_charging", True),
        },
        {
            "key": "media_device_kinds",
            "value": fingerprint.webgl.get("media_device_kinds"),
        },
        {
            "key": "media_devices_hash",
            "value": fingerprint.webgl.get("media_devices_hash"),
        },
        {
            "key": "navigator_permissions_hash",
            "value": fingerprint.webgl.get("navigator_permissions_hash"),
        },
        {"key": "math_fingerprint", "value": fingerprint.webgl.get("math_fingerprint")},
        {
            "key": "supported_math_functions",
            "value": fingerprint.webgl.get("supported_math_functions"),
        },
        {"key": "screen_orientation", "value": "landscape-primary"},
        {
            "key": "rtc_peer_connection",
            "value": int(fingerprint.webgl.get("rtc_peer_connection", "5")),
        },  # type:ignore
        {"key": "4b4b269e68", "value": fingerprint.webgl.get("4b4b269e68")},
        {"key": "6a62b2a558", "value": enforcement_hash},
        {"key": "is_keyless", "value": False},
        {"key": "c2d2015", "value": "29d13b1af8803cb86c2697345d7ea9eb"},
        {"key": "43f2d94", "value": False},
        {"key": "20c15922", "value": True},
        {"key": "4f59ca8", "value": None},
        {
            "key": "speech_default_voice",
            "value": fingerprint.webgl.get(
                "speech_default_voice", "Bulgarian Bulgaria || bg_BG"
            ),
        },
        {
            "key": "speech_voices_hash",
            "value": fingerprint.webgl.get(
                "speech_voices_hash", "b22257aa2722771cf60dbc3aa7b0e2fe"
            ),
        },
        {"key": "4ca87df3d1", "value": "Ow=="},
        {"key": "867e25e5d4", "value": "Ow=="},
        {"key": "d4a306884c", "value": "Ow=="},
    ]

    for item in enhanced_fp_more:
        enhanced_fp.append(item)

    final_fp = [
        {"key": "api_type", "value": "js"},
        {"key": "f", "value": hash.x64hash128(utils.hashable_fe(fe))},
        {
            "key": "n",
            "value": base64.b64encode(str(int(t0)).encode()).decode(),
        },
        {"key": "wh", "value": fingerprint.wh},
        {"key": "enhanced_fp", "value": enhanced_fp},
        {"key": "fe", "value": fe},
        {"key": "ife_hash", "value": hash.x64hash128(", ".join(fe), seed=38)},
        {
            "key": "jsbd",
            "value": f"{{\"HL\":{random.randint(4, 4)},\"NCE\":true,\"DT\":\"\",\"NWD\":\"false\",\"DMTO\":1,\"DOTO\":1}}"
        },
    ]
    encryption_key = f"{user_agent}{arkose.short_esync()}"
    return base64.b64encode(
        arkose.aes_encrypt(
            json.dumps(final_fp, separators=(",", ":")), encryption_key
        ).encode("utf-8")
    ).decode("utf-8")
