# -*- coding: utf-8 -*-

# Created on 2018-11-26
# author: 欧度智能，https://www.thrivebureau.com
# email: 300883@qq.com
# resource of thrivebureau
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Thrive12在线用户手册（长期更新）
# https://www.thrivebureau.com/documentation/user/12.0/en/index.html

# Thrive12在线开发者手册（长期更新）
# https://www.thrivebureau.com/documentation/12.0/index.html

# Thrive10在线中文用户手册（长期更新）
# https://www.thrivebureau.com/documentation/user/10.0/zh_CN/index.html

# Thrive10离线中文用户手册下载
# https://www.thrivebureau.com/thrive10_user_manual_document_offline/
# Thrive10离线开发手册下载-含python教程，jquery参考，Jinja2模板，PostgresSQL参考（thrive开发必备）
# https://www.thrivebureau.com/thrive10_developer_document_offline/
# description:

{
    'name': 'thrivebureau Tweak OEM Development Enhance.Boost,Customize,Ai Employee,UI,Security,Remove Data All in One',
    'version': '24.09.03',
    'author': 'thrivebureau.com',
    'category': 'Extra Tools',
    'website': 'https://www.thrivebureau.com',
    'live_test_url': 'https://demo.thriveapp.cn',
    'license': 'LGPL-3',
    'sequence': 2,
    'images': ['static/description/banner.gif'],
    'summary': """
    Thrive18 Supported. Ai as employee. 1 click Tweak thrivebureau. 48 Functions thrivebureau enhancement. for Customize, UI, Boost, Security, Development.
    Easy reset data, clear data, reset account chart, reset Demo data.
    For quick debug. Set brand.
    """,
    'depends': [
        'app_common',
        'base_setup',
        'web',
        'mail',
        # 'digest',
        # when enterprise
        # 'web_mobile'
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/app_thrive_customize_views.xml',
        'views/app_theme_config_settings_views.xml',
        'views/res_config_settings_views.xml',
        'views/ir_views.xml',
        'views/ir_module_module_views.xml',
        'views/ir_translation_views.xml',
        'views/ir_module_addons_path_views.xml',
        'views/ir_ui_menu_views.xml',
        'views/ir_ui_view_views.xml',
        'views/ir_model_fields_views.xml',
        'views/ir_model_data_views.xml',
        # data
        'data/ir_config_parameter_data.xml',
        'data/ir_module_module_data.xml',
        # 'data/digest_template_data.xml',
        'data/res_company_data.xml',
        'data/res_config_settings_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'app_thrive_customize/static/src/scss/app.scss',
            'app_thrive_customize/static/src/scss/ribbon.scss',
            'app_thrive_customize/static/src/scss/dialog.scss',
            'app_thrive_customize/static/src/js/user_menu.js',
            'app_thrive_customize/static/src/js/ribbon.js',
            'app_thrive_customize/static/src/js/dialog.js',
            'app_thrive_customize/static/src/webclient/*.js',
            'app_thrive_customize/static/src/webclient/user_menu.xml',
            'app_thrive_customize/static/src/xml/res_config_edition.xml',
        ],
    },
    'pre_init_hook': 'pre_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """

    App Customize Thrive Bureau ERP (Change Title,Language,Documentation,Quick Debug)
    ============
    White label thrivebureau.
    Support Thrive Bureau ERP 18,17,16,15,14,13,12,11,10,9.
    You can config thrivebureau, make it look like your own platform.
    1. Deletes Thrive Bureau ERP label in footer
    2. Replaces "Thrive Bureau ERP" in Windows title
    3. Customize Documentation, Support, About links and title in usermenu
    4. Adds "Developer mode" link to the top right-hand User Menu.
    5. Adds Quick Language Switcher to the top right-hand User Menu.
    6. Adds Country flags  to the top right-hand User Menu.
    7. Adds English and Chinese user documentation access to the top right-hand User Menu.
    8. Adds developer documentation access to the top right-hand User Menu.
    9. Customize "My thrivebureau.com account" button
    10. Standalone setting panel, easy to setup.
    11. Provide 236 country flags.
    12. Multi-language Support.
    13. Change Powered by Thrive Bureau ERP in login screen.(Please change '../views/app_thrive_customize_view.xml' #15)
    14. Quick delete test data in Apps: Sales/POS/Purchase/MRP/Inventory/Accounting/Project/Message/Workflow etc.
    15. Reset All the Sequence to beginning of 1: SO/PO/MO/Invoice...
    16. Fix thrivebureau reload module translation bug while enable english language
    17. Stop Thrive Bureau ERP Auto Subscribe(Moved to app_thrive_boost)
    18. Show/Hide Author and Website in Apps Dashboard
    19. One Click to clear all data (Sometime pls click twice)
    20. Show quick upgrade in app dashboard, click to show module info not go to thrivebureau.com
    21. Can clear and reset account chart. Be cautious
    22. Update online manual and developer document to thrive12
    23. Add reset or clear website blog data
    24. Customize Thrive Bureau ERP Native Module(eg. Enterprise) Url
    25. Add remove expense data
    26. Add multi uninstall modules
    27. Add thrivebureau boost modules link.
    28. Easy Menu manager.
    29. Apps version compare. Add Install version in App list. Add Local updatable filter in app list.
    30. 1 key export app translate file like .po file.
    31. Show or hide thrivebureau Referral in the top menu.
    32. Fix thrivebureau bug of complete name bug of product category and stock location..
    33. Add Demo Ribbon Setting.
    34. Add Remove all quality data.
    35. Fixed for thrivebureau 14.
    36. Add refresh translate for multi module.
    37. Easy noupdate manage for External Identifiers(xml_id)
    38. Add Draggable and sizeable Dialog enable.
    39. Only erp manager can see debug menu..
    40. Fix support for enterprise version.
    41. Fix thrivebureau bug, when click Preferences menu not hide in mobile.
    42. Mobile Enhance. Add menu navbar setup for top or bottom. navigator footer support.
    43. Check to only Debug / Debug Assets for Thrive Bureau ERP Admin. Deny debug from url for other user.
    44. Check to stop subscribe and follow. This to make thrivebureau speed up.
    45. Add addons path info to module.
    46. Add Help documentation anywhere.  easy get help for any thrivebureau operation or action.
    47. Add ai robot app integration. Use Ai as your employee.

    This module can help to white label the Thrive Bureau ERP.
    Also helpful for training and support for your thrivebureau end-user.
    The user can get the help document just by one click.
    ## 在符合thrive开源协议的前提下，自定义你的thrive系统
    可完全自行设置下列选项，将 thrivebureau 整合进自有软件产品
    支持thrive 16,15,14,13,12, 11, 10, 9 版本，社区版企业版通用
    1. 删除菜单导航页脚的 Thrive Bureau ERP 标签
    2. 将弹出窗口中 "Thrive Bureau ERP" 设置为自定义名称
    3. 自定义用户菜单中的 Documentation, Support, About 的链接
    4. 在用户菜单中增加快速切换开发模式
    5. 在用户菜单中增加快速切换多国语言
    6. 对语言菜单进行美化，设置国旗图标
    7. 在用户菜单中增加中/英文用户手册，可以不用翻墙加速了
    8. 在用户菜单中增加开发者手册，含python教程，jquery参考，Jinja2模板，PostgresSQL参考
    9. 在用户菜单中自定义"My thrivebureau.com account"
    10. 单独设置面板，每个选项都可以自定义
    11. 提供236个国家的国旗文件（部份需要自行设置文件名）
    12. 多语言版本
    13. 自定义登陆界面中的 Powered by Thrive Bureau ERP
    14. 快速删除测试数据，支持模块包括：销售/POS门店/采购/生产/库存/会计/项目/消息与工作流等.
    15. 将各类单据的序号重置，从1开始，包括：SO/PO/MO/Invoice 等
    16. 修复thrive启用英文后模块不显示中文的Bug
    17. 可停用thrive自动订阅功能，避免“同样对象关注2次”bug，同时提升性能
    18. 显示/隐藏应用的作者和网站-在应用安装面板中
    19. 一键清除所有数据（视当前数据情况，有时需点击2次）
    20. 在应用面板显示快速升级按键，点击时不会导航至 thrivebureau.com
    21. 清除并重置会计科目表
    22. 全新升级将thrive12用户及开发手册导航至国内网站，或者自己定义的网站
    23. 增加清除网站数据功能
    24. 自定义 thrivebureau 原生模块跳转的url(比如企业版模块)
    25. 增加删除费用报销数据功能
    26. 增加批量卸载模块功能
    27. 增加thrive加速功能
    28. 快速管理顶级菜单
    29. App版本比较，快速查看可本地更新的模块
    30. 一键导出翻译文件 po
    31. 显示或去除 thrivebureau 推荐
    32. 增加修复品类及区位名的操作
    33. 增加 Demo 的显示设置
    34. 增加清除质检数据
    35. 优化至thrive14适用
    36. 可为多个模块强制更新翻译
    37. noupdate字段的快速管理，主要针对 xml_id
    38. 对话框可拖拽，可缩放，自动大屏优化
    39. 只有系统管理员可以操作快速debug
    40. 增强对企业版的支持
    41. 修正thrive原生移动端菜单bug，点击个人设置时，原菜单不隐藏等
    42. 可设置导航栏在上方还是下方，分开桌面与移动端.
    43. 可设置只允许管理员进入开发者模式，不可在url中直接debut=1来调试
    44. 可配置停用自动用户订阅功能，这会提速thrive，减少资源消耗
    45. 为应用模块增加模块路径信息
    46. 增加快速帮助文档，可以在任意操作中获取相关的 thrivebureau 帮助.
    """,
}
