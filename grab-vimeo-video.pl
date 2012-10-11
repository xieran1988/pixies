#!/usr/bin/perl 

if (exists $ENV{QUERY_STRING}) {
	$clip = $ENV{QUERY_STRING};
	$fp = '-';
} else {
	$clip = "$ARGV[0]";
	$fp = $ARGV[1];
}
open L, "wget https://player.vimeo.com/video/$clip -O - 2>/dev/null |";
while (<L>) {
	/"signature":"(\w+)"/ && { $sig = $1 };
	/"timestamp":(\d+)/ && { $ts = $1 };
}
$u = "http://player.vimeo.com/play_redirect?quality=sd&codecs=h264&clip_id=$clip&time=$ts&sig=$sig&type=html5_desktop_embed";
system("wget \"$u\" -O $fp 2>/dev/null");
#grep 'signature.:.[[:alnum:]]*' -o i
#`wget $2 -O v/$1.jpg`;
