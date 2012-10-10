#include <stdio.h>
#include <libavcodec/avcodec.h>
//#include <libavcodec/h264.h>
#include <libavformat/avformat.h>
#include <libavutil/avutil.h>
#include <libavutil/dict.h>
#include <jpeglib.h>

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

static AVFormatContext *ifc;
static AVStream *st_h264;
static char *input_filename;

static void init(char *filename) {
	int i;
	input_filename = filename;
	avformat_open_input(&ifc, filename, NULL, NULL);
	printf("nb_streams: %d\n", ifc->nb_streams);
	avformat_find_stream_info(ifc, NULL);
	for (i = 0; i < ifc->nb_streams; i++) {
		AVStream *st = ifc->streams[i];
		AVCodec *c = avcodec_find_decoder(st->codec->codec_id);
		printf("st=%p cid=%d c=%p\n", st, st->codec->codec_id, c);
		printf("%s\n", c->name);
		if (!strcmp(c->name, "h264")) 
			st_h264 = st;
	}
	AVCodec *c = avcodec_find_decoder(st_h264->codec->codec_id);
	i = avcodec_open2(st_h264->codec, c, NULL);
	printf("codec_open %d\n", i);
	st_h264->codec->debug |= FF_DEBUG_PICT_INFO;
}

void poll_frame_and_output_jpg(AVFrame *frm, AVStream *st, char *path) {
	//H264Context *h = st->codec->priv_data;
	int n = 0;
	for (n = 0; n < 1060; n++) {
		AVPacket pkt;
		int i = av_read_frame(ifc, &pkt);
//		printf("read %d, pkt: size=%d index=%d\n", 
//				i, pkt.size, pkt.stream_index);
		if (pkt.stream_index != st->index)
			continue;
		int got_pic; 
		i = avcodec_decode_video2(st->codec, frm, &got_pic, &pkt);
		printf("decode %d, w=%d h=%d\n", i, frm->width, frm->height);
		if (got_pic && frm->key_frame)
			break;
	}

	// YUV420P
	printf("format=%d\n", frm->format);
	printf("key_frame=%d\n", frm->key_frame);
	printf("linesize=%d,%d,%d\n", frm->linesize[0], frm->linesize[1], frm->linesize[2]);

	struct jpeg_compress_struct cinfo;
	struct jpeg_error_mgr jerr;

	FILE *outfile = fopen(path, "wb+");
	cinfo.err = jpeg_std_error(&jerr);
	jpeg_create_compress(&cinfo);
	jpeg_stdio_dest(&cinfo, outfile);
	cinfo.image_width = frm->width; 
	cinfo.image_height = frm->height;
	cinfo.input_components = 3;        
	cinfo.in_color_space = JCS_YCbCr;
	jpeg_set_defaults(&cinfo);
	jpeg_set_quality(&cinfo, 90, TRUE);
	cinfo.raw_data_in = TRUE;
	cinfo.comp_info[0].h_samp_factor = 2; 
	cinfo.comp_info[0].v_samp_factor = 2; 
	cinfo.comp_info[1].h_samp_factor = 1; 
	cinfo.comp_info[1].v_samp_factor = 1; 
	cinfo.comp_info[2].h_samp_factor = 1; 
	cinfo.comp_info[2].v_samp_factor = 1; 
	printf("dct_size=%d\n", DCTSIZE);
	jpeg_start_compress(&cinfo, TRUE);
	int i, j;
	JSAMPROW y[16], cb[16], cr[16];
	JSAMPARRAY data[3];
	data[0] = y;
	data[2] = cb;
	data[1] = cr;
	for (j = 0; j < cinfo.image_height; j += 16) {
		for (i = 0; i < 16; i++) {
			y[i] = frm->data[0] + frm->linesize[0]*(i+j);
			cr[i/2] = frm->data[1] + frm->linesize[1]*((i+j)/2);
			cb[i/2] = frm->data[2] + frm->linesize[2]*((i+j)/2);
		}
		jpeg_write_raw_data(&cinfo, data, 16);
	}
	jpeg_finish_compress(&cinfo);
	fclose(outfile);
	jpeg_destroy_compress(&cinfo);
}

void pick_i_frames_rtmp()
{
	AVFrame *frm = avcodec_alloc_frame();

	int i;
	for (i = 0; i < 8; i++) {
		poll_frame_and_output_jpg(frm, st_h264, "r.jpg");
		printf("GOT IT #%d\n", i);
		sleep(10);
	}
}

void pick_i_frames()
{
	AVStream *st = st_h264;
	int i;

	AVFrame *frm = avcodec_alloc_frame();

	printf("nb_index_entries: %d\n", st->nb_index_entries); 
	for (i = 0; i < st->nb_index_entries; i++) {
		AVIndexEntry *ie = &st->index_entries[i];
//		printf("#%d pos=%lld ts=%lld\n", i, ie->pos, ie->timestamp);
	}

	int nr = st->nb_index_entries;
	int step = nr / 16;
	int ti, seq = 0;

	for (ti = 0; ti < nr; ti += step) {
		int64_t ts = st->index_entries[ti].timestamp;

		seq++;

		printf("ts=%lld\n", ts);
		i = av_seek_frame(ifc, st->index, ts, 0);
		printf("seek %d, index=%d\n", i, st->index);

		//	i = avio_seek(ifc->pb, st->index_entries[1033].pos, SEEK_SET);
		//	printf("io_seek %d\n", i);
		char path[128];
		sprintf(path, "%d.jpg", seq);

		poll_frame_and_output_jpg(frm, st, path);
	}
}

int main()
{
	av_log_set_level(AV_LOG_DEBUG);
	av_register_all();

	init("rtmp://192.168.1.66/myapp/1");
	pick_i_frames_rtmp();
	//init("/root/2.mp4");
//	pick_i_frames();
	return 0;

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

