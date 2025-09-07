import os
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


def get_maya_win():
    win_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)


# -------------------
# Graphics items
# -------------------
class PortItem(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, parent, port_type="input", name="port"):
        radius = 8
        super(PortItem, self).__init__(-radius / 2, -radius / 2, radius, radius, parent)
        self.setBrush(QtGui.QColor(150, 150, 150))
        self.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        self.setZValue(1)
        self.port_type = port_type
        self.name = name
        self.connections = []

        # Label inside node
        self.label = QtWidgets.QGraphicsTextItem(name, parent)
        self.label.setDefaultTextColor(QtCore.Qt.white)
        font = self.label.font()
        font.setPointSize(8)
        self.label.setFont(font)

    def setPosWithLabel(self, x, y):
        self.setPos(x, y)
        if self.port_type == "input":
            # circle is at (x,y) in parent coords; place label inside the node to the right of the circle
            self.label.setPos(x + 12, y - 6)
        else:
            # output: place label inside to the left of the circle
            self.label.setPos(x - 40, y - 6)


class ConnectionItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, start_port, end_port=None):
        super(ConnectionItem, self).__init__()
        self.start_port = start_port
        self.end_port = end_port
        self.setPen(QtGui.QPen(QtCore.Qt.white, 2))
        self.setZValue(-1)  # behind nodes

        # Track on ports
        if self.start_port is not None and self not in self.start_port.connections:
            self.start_port.connections.append(self)
        if self.end_port is not None and self not in self.end_port.connections:
            self.end_port.connections.append(self)

        self.update_path()

    def update_path(self, end_pos=None):
        if not self.start_port:
            return
        start_pos = self.start_port.scenePos()
        if self.end_port:
            end_pos = self.end_port.scenePos()
        elif end_pos is None:
            return

        path = QtGui.QPainterPath(start_pos)
        dx = (end_pos.x() - start_pos.x()) * 0.5
        c1 = QtCore.QPointF(start_pos.x() + dx, start_pos.y())
        c2 = QtCore.QPointF(end_pos.x() - dx, end_pos.y())
        path.cubicTo(c1, c2, end_pos)
        self.setPath(path)

    def detach_from_ports(self):
        # Properly remove self from port connection lists
        if self.start_port and self in self.start_port.connections:
            self.start_port.connections.remove(self)
        if self.end_port and self in self.end_port.connections:
            self.end_port.connections.remove(self)

    def remove(self):
        self.detach_from_ports()
        if self.scene():
            self.scene().removeItem(self)


class NodeItem(QtWidgets.QGraphicsItem):
    def __init__(self, title="Node", width=160, height=80):
        super(NodeItem, self).__init__()
        self.title = title
        self.width = width
        self.height = height
        self.inputs = []
        self.outputs = []
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable |
            QtWidgets.QGraphicsItem.ItemIsSelectable
        )

        # Ports
        if self.title == "BasicStructure":
            out_port = PortItem(self, "output", "Output")
            out_port.setPosWithLabel(self.width - 10, self.height / 2)
            self.outputs.append(out_port)

        if self.title == "Guides":
            in_port = PortItem(self, "input", "Input")
            in_port.setPosWithLabel(10, self.height / 2)
            self.inputs.append(in_port)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        painter.setBrush(QtGui.QColor(40, 40, 40))
        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200), 1))
        painter.drawRoundedRect(rect, 5, 5)
        painter.setBrush(QtGui.QColor(60, 60, 60))
        painter.drawRect(0, 0, self.width, 20)
        painter.setPen(QtCore.Qt.white)
        painter.drawText(5, 15, self.title)

    def itemChange(self, change, value):
        # Keep wires attached while moving
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            for port in self.inputs + self.outputs:
                for c in list(port.connections):
                    c.update_path()
        return super(NodeItem, self).itemChange(change, value)


# -------------------
# View / Editor
# -------------------
class NodeEditorView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(NodeEditorView, self).__init__(parent)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)

        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)

        # Grid
        self._gridSize = 20
        self._gridColor = QtGui.QColor(80, 80, 80)

        # State
        self.available_nodes = ["BasicStructure", "Guides"]
        self.tab_search = None
        self.temp_connection = None
        self.start_port = None

        # Panning
        self.panning = False
        self.last_pan_point = None

    # --------- Helpers
    def _get_item_at(self, pos, cls=None):
        for it in self.items(pos):
            if cls is None or isinstance(it, cls):
                return it
        return None

    def _open_tab_search(self):
        if self.tab_search:
            return

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        label = QtWidgets.QLabel("Available Nodes:")
        list_widget = QtWidgets.QListWidget()
        list_widget.addItems(self.available_nodes)
        list_widget.setCurrentRow(0)  # preselect first item
        line_edit = QtWidgets.QLineEdit()
        line_edit.setPlaceholderText("Type to filter…  (Enter to create, Esc to close)")

        layout.addWidget(label)
        layout.addWidget(list_widget)
        layout.addWidget(line_edit)

        proxy = self.scene.addWidget(container)
        proxy.setPos(self.mapToScene(self.viewport().rect().center()))
        self.tab_search = proxy

        # filtering
        def filter_nodes():
            text = line_edit.text().lower()
            list_widget.clear()
            for node in self.available_nodes:
                if text in node.lower():
                    list_widget.addItem(node)
            if list_widget.count() > 0:
                list_widget.setCurrentRow(0)

        line_edit.textChanged.connect(filter_nodes)

        def create_selected():
            item = list_widget.currentItem()
            if not item:
                return
            node = NodeItem(item.text())
            node.setPos(self.mapToScene(self.viewport().rect().center()))
            self.scene.addItem(node)
            # Close safely after event returns to Qt loop
            QtCore.QTimer.singleShot(0, self._close_tab_search)

        line_edit.returnPressed.connect(create_selected)
        list_widget.itemDoubleClicked.connect(lambda _: create_selected())

        # Esc to close
        def handle_key(ev):
            if ev.key() == QtCore.Qt.Key_Escape:
                QtCore.QTimer.singleShot(0, self._close_tab_search)
            else:
                QtWidgets.QLineEdit.keyPressEvent(line_edit, ev)
        line_edit.keyPressEvent = handle_key

        # focus
        line_edit.setFocus()

    def _close_tab_search(self):
        if self.tab_search:
            proxy = self.tab_search
            self.tab_search = None
            # Remove proxy safely
            if self.scene:
                self.scene.removeItem(proxy)

    # --------- Events
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            if self.tab_search:
                self._close_tab_search()
            else:
                self._open_tab_search()
            return
        super(NodeEditorView, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        # Middle-mouse panning
        if event.button() == QtCore.Qt.MiddleButton:
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            self.panning = True
            self.last_pan_point = event.pos()
            return

        # Delete a connection: Ctrl+Shift+Alt + LMB
        if (event.button() == QtCore.Qt.LeftButton and
                event.modifiers() == (QtCore.Qt.ControlModifier |
                                      QtCore.Qt.ShiftModifier |
                                      QtCore.Qt.AltModifier)):
            conn = self._get_item_at(event.pos(), ConnectionItem)
            if isinstance(conn, ConnectionItem):
                conn.remove()
                return

        # Start a temp connection if we clicked a port
        port = self._get_item_at(event.pos(), PortItem)
        if isinstance(port, PortItem):
            self.start_port = port
            self.temp_connection = ConnectionItem(start_port=port)
            self.scene.addItem(self.temp_connection)

        super(NodeEditorView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.panning and self.last_pan_point:
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()
            # translate the view (screen-space pan)
            self.translate(-delta.x(), -delta.y())
            return

        if self.temp_connection and self.start_port:
            self.temp_connection.update_path(self.mapToScene(event.pos()))

        super(NodeEditorView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Stop panning
        if event.button() == QtCore.Qt.MiddleButton and self.panning:
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.panning = False
            return

        # Finish a connection
        if self.temp_connection and self.start_port:
            end_port = self._get_item_at(event.pos(), PortItem)
            if (isinstance(end_port, PortItem) and
                end_port.port_type == "input" and
                self.start_port.port_type == "output" and
                end_port is not self.start_port):

                self.temp_connection.end_port = end_port
                # add bookkeeping on end port
                if self.temp_connection not in end_port.connections:
                    end_port.connections.append(self.temp_connection)
                self.temp_connection.update_path()

                # Guides input special print
                if end_port.parentItem().title == "Guides":
                    print("Hello")
            else:
                # cancel connection cleanly
                self.temp_connection.detach_from_ports()
                if self.scene():
                    self.scene().removeItem(self.temp_connection)

            self.temp_connection = None
            self.start_port = None

        # Click outside? close tab popup
        if self.tab_search:
            item = self.itemAt(event.pos())
            # If clicked NOT on the popup, close it
            if not isinstance(item, QtWidgets.QGraphicsProxyWidget):
                self._close_tab_search()

        super(NodeEditorView, self).mouseReleaseEvent(event)

    def drawBackground(self, painter, rect):
        super(NodeEditorView, self).drawBackground(painter, rect)
        left = int(rect.left()) - (int(rect.left()) % self._gridSize)
        top = int(rect.top()) - (int(rect.top()) % self._gridSize)
        lines = []
        for x in range(left, int(rect.right()), self._gridSize):
            lines.append(QtCore.QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self._gridSize):
            lines.append(QtCore.QLineF(rect.left(), y, rect.right(), y))
        painter.setPen(QtGui.QPen(self._gridColor, 0.5))
        painter.drawLines(lines)


class GG_NodeEditor(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    TOOL_NAME = "CustomNodeEditor"

    def __init__(self, parent=None):
        delete_workspace_control(self.TOOL_NAME + "WorkspaceControl")
        super(GG_NodeEditor, self).__init__(parent or get_maya_win())
        self.setObjectName(self.TOOL_NAME)
        self.setWindowTitle("Custom Node Editor")
        self.setMinimumSize(800, 600)
        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.node_editor_view = NodeEditorView()

    def create_layout(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.node_editor_view)


# Run it
tool = GG_NodeEditor()
tool.show(dockable=True)
