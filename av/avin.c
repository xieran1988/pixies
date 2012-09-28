#include <stdio.h>
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/avutil.h>
#include <libavutil/dict.h>

typedef struct {
	AVFormatContext *ifc ;
	AVFormatContext *ofc;
	char *name;
	FILE *fp;
} node_t ;

node_t n1, n2, n3, n4;

static void _write_packet(node_t *n, uint8_t *buf, int len)
{
	fwrite(buf, 1, len, n->fp);
}

static int write_packet(node_t *n, uint8_t *buf, int len)
{
//	printf("write_packet: %s %d\n", n->name, len);
	int i;
	fwrite(buf, 1, len, n->fp);
	for (i = 0; i < len; i += 188) {
		//_write_packet(n, buf + i, len);
	}
	return 0;
}

static int write_packet1(void *_d, uint8_t *buf, int len)
{
	return write_packet(&n3, buf, len);
}

static int write_packet2(void *_d, uint8_t *buf, int len)
{
	return write_packet(&n4, buf, len);
}

void node_init(node_t *n, char *filename)
{
	int i, err;

	AVFormatContext *ifc = NULL;
	avformat_open_input(&ifc, filename, NULL, NULL);
	printf("nb_streams: %d\n", ifc->nb_streams);

	AVStream *ist[2];
	ist[0] = ifc->streams[0];
	ist[1] = ifc->streams[1];
	for (i = 0; i < ifc->nb_streams; i++) {
		AVStream *st = ifc->streams[i];
		AVCodec *c = avcodec_find_decoder(st->codec->codec_id);
		printf("%s\n", c->name);
	}

	AVCodec *c[2];

//	AVStream *st = ;
	AVFormatContext *ofc;
	ofc = avformat_alloc_context();
	AVOutputFormat *ofmt = av_guess_format(NULL, "b.ts", NULL);
	ofc->oformat = ofmt;
	strcpy(ofc->filename, "b.ts");

	AVStream *ost[2];
	ost[0] = avformat_new_stream(ofc, NULL);
	ost[0]->codec->codec_type = ist[0]->codec->codec_type;
	ost[0]->codec->codec_id = ist[0]->codec->codec_id;
	avcodec_get_context_defaults3(ost[0]->codec, NULL);
	err = avio_open2(&ofc->pb, "/tmp/b.ts", AVIO_FLAG_WRITE, NULL, NULL);

	printf("write header\n");
	printf("ofc.nb_streams=%d\n", ofc->nb_streams);
	printf("ofc.st[0]=%p\n", ofc->streams[0]);
	printf("ofc.st[0].codec=%p\n", ofc->streams[0]->codec);
	printf("ofc.oformat=%p\n", ofc->oformat);
	printf("ofc.oformat.write_header=%p\n", ofc->oformat->write_header);
	printf("ofc.oformat.name=%s\n", ofc->oformat->name);
	printf("ofc.pb=%p\n", ofc->pb);
	ofc->streams[0]->codec->time_base.num = 10;
	printf("ofc.st[0].codec.timebase={%d,%d}\n", 
			ofc->streams[0]->codec->time_base.num,
			ofc->streams[0]->codec->time_base.den
			);

	avformat_write_header(ofc, NULL);

	n->ifc = ifc;
	n->ofc = ofc;
}

void node_read_packet(node_t *n)
{
	int i;
	AVPacket pkt;
	i = av_read_frame(n->ifc, &pkt);
	if (i < 0) 
		return ;
	if (pkt.stream_index == 0) {
		if (!strcmp(n->name, "src1"))
			printf("%s dts=%llu size=%d\n", n->name, pkt.dts, pkt.size);
		av_write_frame(n->ofc, &pkt);
	}
}

int main()
{
	av_log_set_level(AV_LOG_DEBUG);
	av_register_all();

	n1.name = "src1";
	n2.name = "src2";
	n3.name = "sink1";
	n4.name = "sink2";

	node_init(&n1, "/root/1.mp4");
	node_init(&n2, "/root/2.mp4");
	n1.ofc->pb->write_packet = write_packet1;
	n2.ofc->pb->write_packet = write_packet2;

	n3.fp = fopen("3.ts", "wb+");
	n4.fp = fopen("4.ts", "wb+");

	printf("start read frames\n");

	int n = 0;
	while (n < 140) {
		n++;
		node_read_packet(&n1);
		node_read_packet(&n2);
	}

	return 0;
}

