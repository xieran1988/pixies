#include <types.h>

static inline int convertYUVtoRGB(int y, int u, int v) {
	int r,g,b;

	r = y + (int)1.402f*v;
	g = y - (int)(0.344f*u +0.714f*v);
	b = y + (int)1.772f*u;
	r = r>255? 255 : r<0 ? 0 : r;
	g = g>255? 255 : g<0 ? 0 : g;
	b = b>255? 255 : b<0 ? 0 : b;
	return 0xff000000 | (b<<16) | (g<<8) | r;
}

void yuv2rgb(uint8_t *out, uint8_t *line, int width, int height) {
	int size = width*height;
	int offset = size;
	int u, v, y1, y2, y3, y4;
	int i, k;

	// i percorre os Y and the final pixels
	// k percorre os pixles U e V
	for(i=0, k=0; i < size; i+=2, k+=2) {
		y1 = line[0][i];
		y2 = line[0][i+1];
		y3 = line[0][i];
		y4 = line[0][i+1];

		u = data[offset+k  ]&0xff;
		v = data[offset+k+1]&0xff;
		u = u-128;
		v = v-128;

		out[i  ] = convertYUVtoRGB(y1, u, v);
		out[i+1] = convertYUVtoRGB(y2, u, v);
		out[width+i  ] = convertYUVtoRGB(y3, u, v);
		out[width+i+1] = convertYUVtoRGB(y4, u, v);

		if (i!=0 && (i+2)%width==0)
			i+=width;
	}
}

