#include <stdio.h>
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/avutil.h>
#include <libavutil/dict.h>

static int decode_int_cb(void *a) {
	return 0;
}

int main()
{
	int i, err;

	av_log_set_level(AV_LOG_DEBUG);

	av_register_all();

	AVFormatContext *ifc = NULL;
	avformat_open_input(&ifc, "../a.ts", NULL, NULL);
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
	AVOutputFormat *ofmt = av_guess_format(NULL, "a.ts", NULL);
	ofc->oformat = ofmt;
	strcpy(ofc->filename, "b.ts");

	AVStream *ost[2];
	ost[0] = avformat_new_stream(ofc, NULL);
	ost[0]->codec->codec_type = ist[0]->codec->codec_type;
	ost[0]->codec->codec_id = ist[0]->codec->codec_id;
	avcodec_get_context_defaults3(ost[0]->codec, NULL);
	AVIOInterruptCB cb = { decode_int_cb, NULL} ;
	ofc->interrupt_callback = cb;
	err = avio_open2(&ofc->pb, "b.ts", AVIO_FLAG_WRITE, NULL, NULL);

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

	printf("read frames\n");

	int n = 0;
	while (n < 22) {
		n++;
		AVPacket pkt;
		i = av_read_frame(ifc, &pkt);
		if (i < 0) break;
		if (pkt.stream_index == 0) {
			printf("#%d dts=%llu size=%d\n", n, pkt.dts, pkt.size);
			av_write_frame(ofc, &pkt);
		}
	}

	return 0;
}

