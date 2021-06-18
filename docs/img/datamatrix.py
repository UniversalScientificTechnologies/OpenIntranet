from pystrich.datamatrix import DataMatrixEncoder

a = '[)>\u001E06\u001DL5c70984512875079b91f8949\u001DT5c70984512875079b91f8949\u001D1P5c70984512875079b91f8949\u001D5D201229\u001E\u0004'

encoder = DataMatrixEncoder(a)
encoder.save("datamatrix.packet.png")
