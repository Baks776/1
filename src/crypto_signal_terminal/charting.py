from __future__ import annotations

import numpy as np
import pandas as pd

try:
    import pyqtgraph as pg
    from PySide6.QtWidgets import QWidget
except ImportError:  # pragma: no cover
    pg = None
    QWidget = object


if pg:

    class CandlestickItem(pg.GraphicsObject):
        def __init__(self, data):
            super().__init__()
            self.data = data
            self.picture = None
            self.generate_picture()

        def generate_picture(self):
            picture = pg.QtGui.QPicture()
            painter = pg.QtGui.QPainter(picture)
            width = 0.6
            for x, open_, high, low, close in self.data:
                painter.setPen(pg.mkPen("w"))
                painter.drawLine(pg.QtCore.QPointF(x, low), pg.QtCore.QPointF(x, high))
                color = (0, 170, 0) if close >= open_ else (200, 50, 50)
                painter.setBrush(pg.mkBrush(color))
                painter.drawRect(pg.QtCore.QRectF(x - width / 2, open_, width, close - open_ or 0.0001))
            painter.end()
            self.picture = picture

        def paint(self, painter, *args):
            painter.drawPicture(0, 0, self.picture)

        def boundingRect(self):
            return pg.QtCore.QRectF(self.picture.boundingRect())


    class ChartWidget(pg.GraphicsLayoutWidget):
        def __init__(self):
            super().__init__()
            self.price_plot = self.addPlot(row=0, col=0)
            self.price_plot.showGrid(x=True, y=True, alpha=0.2)
            self.price_plot.addLegend()
            self.nextRow()
            self.equity_plot = self.addPlot(row=1, col=0)
            self.equity_plot.showGrid(x=True, y=True, alpha=0.2)
            self.equity_plot.setLabel("left", "Equity")

        def set_price_data(self, df: pd.DataFrame):
            self.price_plot.clear()
            if df.empty:
                return
            xs = np.arange(len(df))
            candle_data = list(zip(xs, df["open"].values, df["high"].values, df["low"].values, df["close"].values))
            candles = CandlestickItem(candle_data)
            self.price_plot.addItem(candles)
            self.price_plot.plot(xs, df["ema_fast"].values, pen=pg.mkPen("#f5a623", width=1), name="EMA Fast")
            self.price_plot.plot(xs, df["ema_mid"].values, pen=pg.mkPen("#50e3c2", width=1), name="EMA Mid")
            self.price_plot.plot(xs, df["ema_slow"].values, pen=pg.mkPen("#4a90e2", width=1), name="EMA Slow")

            long_idx = df.index[df["long_signal"]].tolist()
            short_idx = df.index[df["short_signal"]].tolist()
            if long_idx:
                pos = [df.index.get_loc(i) for i in long_idx]
                self.price_plot.plot(
                    pos,
                    df.loc[long_idx, "close"].values,
                    pen=None,
                    symbol="t1",
                    symbolBrush=pg.mkBrush(0, 220, 100),
                    symbolSize=10,
                )
            if short_idx:
                pos = [df.index.get_loc(i) for i in short_idx]
                self.price_plot.plot(
                    pos,
                    df.loc[short_idx, "close"].values,
                    pen=None,
                    symbol="t",
                    symbolBrush=pg.mkBrush(220, 90, 90),
                    symbolSize=10,
                )

        def set_equity_curve(self, equity: list[float]):
            self.equity_plot.clear()
            if equity:
                self.equity_plot.plot(np.arange(len(equity)), np.array(equity), pen=pg.mkPen("#ffd166", width=2))

else:

    class ChartWidget(QWidget):  # type: ignore[misc]
        def __init__(self):
            raise RuntimeError("pyqtgraph is not installed. Install with: pip install pyqtgraph")
