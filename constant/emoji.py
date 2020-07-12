
NB = ([str(i.to_bytes(1, 'big') + b'\xef\xb8\x8f\xe2\x83\xa3', encoding='utf-8') for i in range(48, 58)] + ["🔟"] +
      [str(b'\xf0\x9f\x87' + i.to_bytes(1, 'big'), encoding='utf-8') for i in range(0xa7, 0xc0)])