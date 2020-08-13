from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, \
    QFontDialog, QFileDialog, QColorDialog
from PySide2.QtCore import QPoint
from PySide2.QtGui import QFont, QColor, QIcon, QFontDatabase, QPalette
from box_widget import *
from document import Document
import os
import re
from test import test  # 测试
import globalvars
import sys

GlobalVars = globalvars.GlobalVars


class DocumentScrollArea(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumSize(GlobalVars.PageWidth + 30, 10000)
        self.setMinimumSize(GlobalVars.PageWidth + 30, 10)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setStyleSheet("background-color:rgba(255,255,255)")

    def setDocument(self, document):
        self.document = document
        self.setWidget(document)


class FontFamiliesPanel(ListWidget):
    """
    字体选项栏
    """

    def __init__(self, parent=None, func=None):  # 最后选择的字体通过font返回,func表示字体选择的时候，执行的函数
        super().__init__(parent)
        self.func = func  # func表示选中字体后要进行的操作
        fontDataBase = QFontDatabase().families()
        fontDataBase.reverse()  # 反转列表，使得中文位于前面
        for f in fontDataBase:
            button = PushButton(f)
            button.clicked.connect(self.itemClicked(f))  # 不能直接用 lambda f=f:self.func(f) 不知道为什么
            font = QFont(f, pointSize=10)
            button.setFont(font)  # 设置字体
            button.resize(button.sizeHint())
            self.addItem(button)
        self.hide()

    def itemClicked(self, f):
        return lambda: self.func(f)


class FontSizePanel(ListWidget):
    """
    字体大小选择栏
    """

    def __init__(self, parent=None, func=None):
        super().__init__(parent)
        self.func = func
        pointSize = [10, 12, 14, 16, 20, 24, 30]  # 预先定义的不同的字体大小

        for s in pointSize:
            button = PushButton(str(s))
            button.clicked.connect(self.itemClicked(s))
            button.setFont(QFont(button.font().family(), pointSize=s))
            button.resize(button.sizeHint())
            self.addItem(button)
        self.hide()  # 默认不显示

    def itemClicked(self, s):
        return lambda: self.func(s)


# 行距选择栏
class LineSpacingPanel(ListWidget):
    """
    行距选择栏
    """

    def __init__(self, parent=None, func=None):
        super().__init__(parent)
        self.func = func
        pointSize = [0.25, 0.5, 1, 5, 10, 20]  # 预先定义的不同的行距大小,小数主要服务相对行距

        for s in pointSize:
            button = PushButton(str(s))
            button.clicked.connect(self.itemClicked(s))
            button.resize(button.sizeHint())
            self.addItem(button)
        self.hide()  # 默认不显示

    def itemClicked(self, s):
        return lambda: self.func(s)


class TitleLevelsPanel(ScrollArea):
    """
    标题选项栏
    """

    def __init__(self, parent=None, func=None):  # func 字体选择执行的程序
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.func = func
        self.titleButtons = {}  # 显示当前标题等级时候使用
        self.ActivatedTitleButton = None  # 当前激活的标题等级

        layout = QGridLayout()
        row = column = 0  # 起始的行和列的位置
        for t in GlobalVars.TitleLevels:
            button = PushButton(t.name, self)
            # button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.titleButtons[t.name] = button
            button.setFont(t.font)
            button.clicked.connect(self.itemClicked(t))
            layout.addWidget(button, row, column)
            if column == 4:  # 换行，每行最多容纳四个标题
                row += 1
            else:
                column += 1
        self.setLayout(layout)

    def itemClicked(self, titleLevel):  # 选择字体
        def clicked():
            if self.func:
                self.func(titleLevel)  # 选择字体的时候执行的额操作
            GlobalVars.CurrentTitleLevel = titleLevel

        return clicked

    def setTitle(self, t):  # 更新当前的标题等级
        if self.ActivatedTitleButton:  # 恢复之前的标题格式，待优化，太冗长
            self.ActivatedTitleButton.setStyleSheet(
                "QPushButton{{background-color:rgba{};border:0px}} QPushButton:hover{{background-color:rgba{}}} ".format(
                    str(GlobalVars.Panel_BackgroundColor.getRgb()), str(GlobalVars.Panel_ActivateColor.getRgb())))
        self.ActivatedTitleButton = self.titleButtons[t.name]  # 设置新的当前标题
        self.ActivatedTitleButton.setStyleSheet(
            "QPushButton{{background-color:rgba{};border:0px}} ".format(str(GlobalVars.Panel_ActivateColor.getRgb())))


class ToolWidget(QWidget):
    """
    # 文字工具栏
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.DocWidget = parent
        self.setFocusPolicy(Qt.NoFocus)
        self.ui()

    def ui(self):
        self.setMaximumSize(10000, 100)  # 限制高度
        self.setMinimumSize(10, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.mainLayout = QHBoxLayout()  # 总体布局

        # 文件管理布局
        saveButton = ToolButton(QIcon("../../images/save.png"), "", toolTip="保存", clicked=self.saveDocument,shortcut="ctr+s")
        saveAsButton = ToolButton(QIcon("../../images/saveas.png"), "", toolTip="另存为", clicked=self.saveDocumentAs,shortcut="ctr+shift+s")
        openButton = ToolButton(QIcon("../../images/open.png"), "", toolTip="打开", clicked=self.openDocument,shortcut="ctr+o")
        newButton = ToolButton(QIcon("../../images/new.png"), "", toolTip="新建")

        fileLayout = QGridLayout()
        fileLayout.addWidget(newButton, 0, 0)
        fileLayout.addWidget(openButton, 0, 1)
        fileLayout.addWidget(saveButton, 1, 0)
        fileLayout.addWidget(saveAsButton, 1, 1)

        # 字体布局
        GlobalVars.titleLevelsPanel = TitleLevelsPanel(func=self.setTitleLevel)  # func绑定到函数，修改标题等级时候调用
        GlobalVars.CurrentTitleLevel = GlobalVars.CurrentTitleLevel  # 重新赋值，刷新界面

        GlobalVars.currentFontFamilyPanel = LineEditWithSubButton(self, toolTip="选择字体", subButton="itemButton")
        GlobalVars.currentFontFamilyPanel.listWidget = FontFamiliesPanel(self.parent(), func=self.setFontFamily)

        GlobalVars.currentFontSizePanel = LineEditWithSubButton(self, toolTip="字体大小", subButton="itemButton")
        GlobalVars.currentFontSizePanel.listWidget = FontSizePanel(self.parent(), func=self.setFontSize)

        # 斜体设置
        GlobalVars.currentFontItalicPanel = ToolButton(clicked=self.setFontItalic, subButton="itemButton")  # 斜体面板
        GlobalVars.currentFontItalicPanel.listWidget.addItem(
            ToolButton(icon=QIcon("../../images/italic.png"), toolTip="斜体", clicked=lambda: self.setFontItalic(True)))
        GlobalVars.currentFontItalicPanel.listWidget.addItem(
            ToolButton(icon=QIcon("../../images/notitalic.png"), toolTip="取消斜体",
                       clicked=lambda: self.setFontItalic(False)))

        GlobalVars.currentFontItalicPanel.listWidget.setParent(self.parent())  # 设置父对象
        # 粗体设置 待完善，不同的粗度
        GlobalVars.currentFontWeightPanel = ToolButton(self, clicked=self.setFontWeight, subButton="itemButton")  # 加粗面板
        GlobalVars.currentFontWeightPanel.listWidget.addItem(
            ToolButton(icon=QIcon("../../images/bold.png"), toolTip="加粗",
                       clicked=lambda: self.setFontWeight(QFont.Bold)))
        GlobalVars.currentFontWeightPanel.listWidget.addItem(
            ToolButton(icon=QIcon("../../images/unbold.png"), toolTip="取消加粗",
                       clicked=lambda: self.setFontWeight(False)))
        GlobalVars.currentFontWeightPanel.listWidget.setParent(self.parent())  # doc是listwidget的父级
        GlobalVars.CurrentFont = GlobalVars.CurrentFont  # 更新与文字相关属性面板

        GlobalVars.currentTextColorPanel = ToolButton("A", toolTip="设置文字颜色", clicked=self.setTextColor)
        GlobalVars.CurrentTextColor = GlobalVars.CurrentTextColor  # 重新赋值，刷新界面

        GlobalVars.currentBackgroundColorPanel = ToolButton(toolTip="设置背景色", clicked=self.setBackgroundColor)
        GlobalVars.CurrentBackgroundColor = GlobalVars.CurrentBackgroundColor  # 重新赋值，刷新界面

        GlobalVars.currentKeyWordStatusPanel = ToolButton("关", toolTip="设置为关键字")  # 待完善
        GlobalVars.currentKeyWordStatusPanel.setEnabled(False)
        GlobalVars.currentLinkStatusPanel = ToolButton("链", toolTip="设置为超链接")  # 待完善
        GlobalVars.currentLinkStatusPanel.setEnabled(False)

        GlobalVars.currentFontSuperScriptPanel = ToolButton(icon=QIcon("../../images/superscript.png"),
                                                            toolTip="上标")  # 上标待完善
        GlobalVars.currentFontSuperScriptPanel.setEnabled(False)
        GlobalVars.currentFontSubScriptPanel = ToolButton(icon=QIcon("../../images/subscript.png"),
                                                          toolTip="下标")  # 下标待完善
        GlobalVars.currentFontSubScriptPanel.setEnabled(False)

        font1Layout = QHBoxLayout()
        font1Layout.addWidget(GlobalVars.currentFontFamilyPanel)
        font1Layout.addWidget(GlobalVars.currentFontSizePanel)
        font2Layout = QHBoxLayout()
        font2Layout.addWidget(GlobalVars.currentKeyWordStatusPanel)
        font2Layout.addWidget(GlobalVars.currentLinkStatusPanel)
        font2Layout.addWidget(GlobalVars.currentFontSuperScriptPanel)
        font2Layout.addWidget(GlobalVars.currentFontSubScriptPanel)
        font2Layout.addWidget(GlobalVars.currentFontItalicPanel)
        font2Layout.addWidget(GlobalVars.currentFontWeightPanel)
        font2Layout.addWidget(GlobalVars.currentTextColorPanel)
        font2Layout.addWidget(GlobalVars.currentBackgroundColorPanel)
        fontLayout = QVBoxLayout()
        fontLayout.addLayout(font1Layout)
        fontLayout.addLayout(font2Layout)

        # 段落相关设置
        GlobalVars.alignLeftPanel = ToolButton(QIcon("../../images/alignleft.png"), "", toolTip="左对齐")  # 待完善
        GlobalVars.alignLeftPanel.setEnabled(False)
        GlobalVars.alignCenterPanel = ToolButton(QIcon("../../images/aligncenter.png"), "", toolTip="中对齐")  # 待完善
        GlobalVars.alignCenterPanel.setEnabled(False)
        GlobalVars.alignRightPanel = ToolButton(QIcon("../../images/alignright.png"), "", toolTip="右对齐")  # 待完善
        GlobalVars.alignRightPanel.setEnabled(False)

        GlobalVars.currentLineSpacingPanel = LineEditWithSubButton(toolTip="设置行距大小", subButton="itemButton")
        GlobalVars.currentLineSpacingPanel.listWidget = LineSpacingPanel(self.parent(), func=self.setLineSpacing)
        GlobalVars.CurrentLineSpacing = GlobalVars.CurrentLineSpacing

        GlobalVars.currentLineSpacingPolicyPanel = ToolButton(clicked=self.setLineSpacingPolicy,
                                                              subButton="itemButton")
        GlobalVars.currentLineSpacingPolicyPanel.listWidget.addItem(
            ToolButton(icon=QIcon("../../images/absolute_linespacing.png"), toolTip="绝对行距",
                       clicked=lambda: self.setLineSpacingPolicy(GlobalVars.absLineSpacingPolicy)))
        GlobalVars.currentLineSpacingPolicyPanel.listWidget.addItem(
            ToolButton(icon=QIcon("../../images/relative_linespacing.png"), toolTip="相对行距",
                       clicked=lambda: self.setLineSpacingPolicy(GlobalVars.relLineSpacingPolicy)))
        GlobalVars.currentLineSpacingPolicyPanel.listWidget.setParent(self.parent())
        GlobalVars.CurrentLineSpacingPolicy = GlobalVars.CurrentLineSpacingPolicy  # 更新界面

        paragraph1Layout = QHBoxLayout()
        paragraph1Layout.addWidget(GlobalVars.currentLineSpacingPanel)
        paragraph2Layout = QHBoxLayout()
        paragraph2Layout.addWidget(GlobalVars.alignLeftPanel)
        paragraph2Layout.addWidget(GlobalVars.alignCenterPanel)
        paragraph2Layout.addWidget(GlobalVars.alignRightPanel)
        paragraph2Layout.addWidget(GlobalVars.currentLineSpacingPolicyPanel)
        paragraphLayout = QVBoxLayout()
        paragraphLayout.addLayout(paragraph1Layout)
        paragraphLayout.addLayout(paragraph2Layout)

        self.mainLayout.addLayout(fileLayout)
        self.mainLayout.addWidget(GlobalVars.titleLevelsPanel)
        self.mainLayout.addLayout(fontLayout)
        self.mainLayout.addLayout(paragraphLayout)

        self.setLayout(self.mainLayout)

        self.setAutoFillBackground(True)
        pal = QPalette()
        pal.setColor(QPalette.Background, GlobalVars.Panel_BackgroundColor)
        self.setPalette(pal)

    def saveDocument(self):
        document = GlobalVars.CurrentDocument
        if not document.path:
            if document.title:
                file, format = QFileDialog.getSaveFileName(self, "保存文件", "../../files/" + document.title,
                                                           "网页格式(*.html);;所有(*)")
            else:
                file, format = QFileDialog.getSaveFileName(self, "保存文件", "../../files/document", "网页格式(*.html);;所有(*)")

            if file:
                if not document.title:  # 标题没有命名,自动定义文档标题
                    document.title = os.path.basename(file).split(".")[0]
                document.path = file
            else:
                return  # 不可少
        with open(document.path, "w", encoding="UTF-8") as f:
            f.write(document.toHtml())

    def saveDocumentAs(self):
        document = GlobalVars.CurrentDocument
        path = document.path
        if path:
            name, suffix = os.path.basename(path).split(".")  # 名字和后缀
            newPath = os.path.dirname(path) + name + "1." + suffix

            file, format = QFileDialog.getSaveFileName(self, "保存文件", newPath, "网页格式(*.html);;所有(*)")

            if file:
                with open(file, "w", encoding="UTF-8") as f:
                    f.write(document.toHtml())
                # 待完善 ，关闭旧文档，打开新文档
        else:
            self.saveDocument()

    def openDocument(self):
        # 待完善，判断是否保存现有文档或者新建文档选项卡
        file, suffix = QFileDialog.getOpenFileName(self, "打开文件", "../../files", "网页格式(*.html)")
        if file:
            with open(file, "r", encoding="UTF-8") as f:
                document = self.analysisHtml(f)  # 解析html文档
                document.path = file
                self.DocWidget.documentScrollArea.setWidget(document)
                self.update()
                print(True)

    def setTextColor(self):
        color = QColorDialog.getColor(GlobalVars.CurrentTextColor, self, title="选择文字颜色")
        GlobalVars.CurrentTextColor = color
        if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态 待优化，多个段落反复更新坐标降低性能
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setTextColor"):
                    block.setTextColor(color)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setTextColor"):
                GlobalVars.CurrentBlock.setTextColor(color)

    def setBackgroundColor(self):
        color = QColorDialog.getColor(GlobalVars.CurrentBackgroundColor, self, title="选择背景颜色")
        GlobalVars.CurrentBackgroundColor = color
        if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setBackgroundColor"):
                    block.setBackgroundColor(color)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setBackgroundColor"):
                GlobalVars.CurrentBlock.setBackgroundColor(color)

    def setFont_(self):
        font, ok = QFontDialog.getFont()
        if ok:
            GlobalVars.CurrentFont = font
            if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态
                for block in GlobalVars.CurrentDocument.SelBlocks:
                    if hasattr(block, "setFont_"):
                        block.setFont_(font)
            else:
                if hasattr(GlobalVars.CurrentBlock, "setFont_"):
                    GlobalVars.CurrentBlock.setFont_(font)

    def setFontFamily(self, family):
        font = QFont(GlobalVars.CurrentFont)
        font.setFamily(family)
        GlobalVars.CurrentFont = font  # 更新当前字体
        if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setFontFamily"):
                    block.setFontFamily(family)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setFontFamily"):
                GlobalVars.CurrentBlock.setFontFamily(family)
        GlobalVars.currentFontFamilyPanel.listWidget.hide()

    def setFontItalic(self, italic=None):
        if italic is None:
            italic = not GlobalVars.CurrentFont.italic()
        font = QFont(GlobalVars.CurrentFont)
        font.setItalic(italic)
        GlobalVars.CurrentFont = font  # 刷新界面
        if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setFontItalic"):
                    block.setFontItalic(italic)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setFontItalic"):
                GlobalVars.CurrentBlock.setFontItalic(italic)
        GlobalVars.currentFontItalicPanel.listWidget.hide()

    def setFontWeight(self, weight=None):
        if weight is None:
            weight = False if GlobalVars.CurrentFont.bold() else QFont.Bold
        font = QFont(GlobalVars.CurrentFont)
        font.setWeight(weight)
        GlobalVars.CurrentFont = font  # 刷新界面
        if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setFontWeight"):
                    block.setFontWeight(weight)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setFontWeight"):
                GlobalVars.CurrentBlock.setFontWeight(weight)
        GlobalVars.currentFontWeightPanel.listWidget.hide()  # 隐藏字体粗度选项栏

    def setFontSize(self, size):
        font = QFont(GlobalVars.CurrentFont)
        font.setPointSize(size)
        GlobalVars.CurrentFont = font  # 刷新界面
        if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setFontSize"):
                    block.setFontSize(size)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setFontSize"):
                GlobalVars.CurrentBlock.setFontSize(size)
        GlobalVars.currentFontSizePanel.listWidget.hide()  # 隐藏字体粗度选项栏

    # 设置标题
    def setTitleLevel(self, titleLevel):
        GlobalVars.CurrentTitleLevel = titleLevel
        if GlobalVars.CurrentDocument.SelBlocks:  # 选中状态
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setTitleLevel"):
                    block.setTitleLevel(titleLevel)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setTitleLevel"):
                GlobalVars.CurrentBlock.setTitleLevel(titleLevel)

    def setLineSpacing(self, spacing):
        GlobalVars.CurrentLineSpacing = spacing
        if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setLineSpacing"):
                    block.setLineSpacing(spacing)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setLineSpacing"):
                GlobalVars.CurrentBlock.setLineSpacing(spacing)
        GlobalVars.currentLineSpacingPanel.listWidget.hide()

    def setLineSpacingPolicy(self, policy=None):
        if not policy:
            if GlobalVars.CurrentLineSpacingPolicy is GlobalVars.relLineSpacingPolicy:
                policy = GlobalVars.absLineSpacingPolicy
            else:
                policy = GlobalVars.relLineSpacingPolicy
        GlobalVars.CurrentLineSpacingPolicy = policy
        if GlobalVars.CurrentDocument.SelBlocks:  # 处于选中状态
            for block in GlobalVars.CurrentDocument.SelBlocks:
                if hasattr(block, "setLineSpacingPolicy"):
                    block.setLineSpacingPolicy(policy)
        else:
            if hasattr(GlobalVars.CurrentBlock, "setLineSpacingPolicy"):
                GlobalVars.CurrentBlock.setLineSpacingPolicy(policy)
        GlobalVars.currentLineSpacingPolicyPanel.listWidget.hide()

    # 解析html格式 待优化,用beautifulsoap
    def analysisHtml(self, f):
        document = Document()
        text = f.readline()
        while text:
            if text.startswith("<body"):
                document.documentWidth = int(self.analysisStyle(text)["width"][:-2])  # 去掉px字符
            if text.startswith("<title"):
                document.title = self.analysisText(text)
            if text.startswith("<h1") or text.startswith("<h2") or text.startswith("<h3") or text.startswith("<h4"):
                block = document.addTextBlock()
                text_ = self.analysisText(text)  # 文本内容

                block.addTextItem(text_, preTextItem=None)
                exec("block.setTitleLevel_(GlobalVars.T{})".format(text[2]))
            if text.startswith("<p"):
                block = document.addTextBlock()
            if text.startswith("<span"):
                attr = self.analysisStyle(text)  # 属性
                text = self.analysisText(text)  # 文本内容

                font = QFont()
                font.setFamily(attr["font-family"])
                font.setPointSize(int(attr["font-size"][0:-2]))

                textColor = attr["color"]
                textColor = textColor[5:-1].split(",")
                textColor = [int(textColor[i]) for i in range(3)] + [int(float(textColor[3]) * 255)]
                textColor = QColor(*textColor)

                backgroundColor = attr["background-color"]
                if backgroundColor == "none":
                    backgroundColor = None
                else:
                    backgroundColor = backgroundColor[5:-1].split(",")
                    backgroundColor = [int(backgroundColor[i]) for i in range(3)] + [
                        int(float(backgroundColor[3]) * 255)]
                    backgroundColor = QColor(*backgroundColor)

                block.addTextItem(text, font=font, textColor=textColor, backgroundColor=backgroundColor)
            text = f.readline()
        return document

    # 分析html的style属性，返回字典
    def analysisStyle(self, text):
        text = re.search('style=".*"', text).group()  # style字段
        attr = text[text.find('"') + 1:text.rfind('"')]  # 属性字段
        attr = dict((i.split(":") for i in attr.split(";")))  # 属性转化为字典
        return attr

    # 分析html的字段，返回文字内容，限制在同一行
    def analysisText(self, text):
        text = re.search(">.*<", text).group()
        text = text.strip(">")
        text = text.lstrip("<")
        return text


class DocWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        initialize()  # 初始化一些参数
        self.ui()

    def ui(self):
        self.setWindowIcon(QIcon("../../images/icon.png"))
        self.setWindowTitle("Doc")

        self.toolWidget = ToolWidget(self)
        self.toolWidget.move(0, 0)

        self.documentScrollArea = DocumentScrollArea(self)
        self.document = Document(self)
        self.documentScrollArea.setDocument(self.document)
        self.document.addTextBlockWithTextItem()  # 初始化

        layout = QVBoxLayout()
        layout.addWidget(self.toolWidget)
        documentLayout = QHBoxLayout()
        documentLayout.addStretch()
        documentLayout.addWidget(self.documentScrollArea)
        documentLayout.addStretch()
        layout.addLayout(documentLayout)
        self.setLayout(layout)

        self.setGeometry(200, 200, 1500, 800)  # 默认尺寸


def initialize():
    # 之所以将有关文字的内容放到这里，在其他地方定义后，计算pointsize会出错
    GlobalVars.CurrentFont = QFont("微软雅黑", pointSize=12)

    # 标题格式待完善，从设置提取
    GlobalVars.T0 = globalvars.TitleLevel("正文", QFont("微软雅黑", pointSize=12, ), toHtmlFormat="p")
    GlobalVars.T1 = globalvars.TitleLevel("一级标题", QFont("微软雅黑", pointSize=20, weight=QFont.Bold), toHtmlFormat="h1")
    GlobalVars.T2 = globalvars.TitleLevel("二级标题", QFont("微软雅黑", pointSize=16, weight=QFont.Bold), toHtmlFormat="h2")
    GlobalVars.T3 = globalvars.TitleLevel("三级标题", QFont("微软雅黑", pointSize=14, weight=QFont.Bold), toHtmlFormat="h3")
    GlobalVars.T4 = globalvars.TitleLevel("四级标题", QFont("微软雅黑", pointSize=12, weight=QFont.Bold), toHtmlFormat="h4")
    GlobalVars.CurrentTitleLevel = GlobalVars.T0  # 默认为正文格式


def main():
    app = QApplication(sys.argv)
    doc = DocWidget()
    doc.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
