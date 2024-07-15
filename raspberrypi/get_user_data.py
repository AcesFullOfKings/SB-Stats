import sqlite3
import os 
import json
import requests

from time import time
	
categories = ["filler", "intro", "outro", "sponsor", "selfpromo", "preview", "interaction", "nonmusic"]
expanded_categories = {'s': 'sponsor', 'u': 'selfpromo', 'i': 'intro', 'o': 'outro', 'p': 'preview', 'r': 'interaction', 'h': 'poi_highlight', 'e': 'exclusive_access', 'f': 'filler', 'c': 'chapter', 'n': 'nonmusic'}
expanded_types = {'f': 'full', 's': 'skip', 'm': 'mute', 'p': 'poi', 'c': 'chapter'}

VIP_userIDs = ['57ddecc5b36813ddb8ea1eba73342c8a783527b884b6ebcb177bf37cafce7620', 'c4a6408834ac21d6bd8eca3cee787a1b1c3009ffacb1d481512424ad1f1be8f2', 'd261c35ce21b0554c183fc42e2f92bf30609e0540bad8e4a94e9df5293b6e617', '963cdc21439055c825860792fa6ef0a48ffc8823f20f31a676ea41755c8e00b7', '7b89ea26f77bda8176e655eee86029f28c1e6514b6d6e3450bce362b5b126ca3', 'a09c69582e96125ea57c73d499291ddf56049b8de873f829553bf2150a8f39ce', '23e80b03616433c784ea7b0c0406124d85c48c08297168eb0cc9281b5ceb36cb', 'ef6cf405af6341847e9df9fbb3c2c90ba00a10fa76008ed6240e5ccb25f50bc9', '70ed836da4865b2c9b01f19f24730345fec5f91989c3ddd5f46770200f841126', 'd1ecbc79b2f200436c774c015fbac8660d4a2009b8b717393e345cc657c1346f', '9ea723c057c922179ac98ab79742ce39b8eaa59ac5351162b45c1dce86e0b96a', 'd3c5d3dc8bb01c565f5bef193e39799a36b90dd3f0d3673faee72bb516ec7d60', '05f9bf1b4831b3f15dfb30cd4f88ba031aba0b32ab8b9ab4816abf0ebd51af67', '38c040ce69a60b44d5b76c887f54def0a788b0e5f37d149e3c9271c74fc004b0', '58cc24de737a926d51535f9bc2364f7d28356aa1c7aeb85544bd8232fe2ce177', '42f6f6aea4ccc62bb4f791d11df5cc7f05811042d3fed2d9ec009297d3212f6e', 'b1a5175b47bcde123c7ddfb73b63d36e5db475f64d05f0a1a4a4e2db6a4cee06', 'dbdecfb949384ed680446ef8e04a77a3110746d560514fb3bf7134943888ee35', '040cd2877a3a9d3aa8786e97c50fe69644df371c4b0ce8a19796b17f74220529', 'c2c425f2bda5ab4715aa19827df6bf85676a08e574b15900cbc79a681c1b565d', 'f285552fa2320f86b7125b089f9802859447afbed514c0e98e0dc15545eeb69a', 'c649ea669fcba7c9e5f66406f2bc3efdf04afaf6013ee86820499387df58e349', 'a8770a376773d0679b557b1409bd45141f765ed926fca65cf8b030f8e5561168', '6d74edf9f025c3273c2db36664374f5edfdf4e45142068480d12b197957f0398', 'd742d4134301b513efd1fc758d8ed0a3a1fc71737476332cae64d8898df33ba8', 'd3b7e2271732fd95460fcd454bd4673940b95237baa1a06da19db82c07073eab', '41a44cb5697f1aba6bd0618f0707b9899e7eae9181c147bb927dc79ac8028021', '20bb74bc59a43defbd8995e0e7c675fbabd375dfe79ed0d0456e363ba6089633', '21487770b5f19986aad65c7aeffa8fb1d664e2765d85ad6f6a756a98bee0319f', '1a3cb3d1f0aa7ffc28e9554a19d8192f0f08a56c5ae5c6880d431f66d2bbd900', 'fe8069157df246ab3db38479fce97e5ac3ea22b16f2eb853590af68235d4d479', 'ef5298382071c42d6edd4abd8239bb88f0cef28ab35adfd7f79e80b47da533dc', '695deaba9d56d74fc5b53c127f3bbaf6d25ae511b92ffe85b917c7436d78abf2', '7a7e6f513cd2a7a9abfd5c3dec7c8e2ea0e5e26f2683a83342ebad0f68d7754e', '6bf14387297df3152584ae95d6682cdc98cfee30c1e8a6a4ad876babdfee555b', '107fad6fbc17ede2ce696c29eb59e98d97edbbe69e4c411132135301a9251631', 'ef20065c44aa145423351b482eb7cfff598538f945607769b97ddd46422b68ea', '5bacbb875e2033683aac7d520fa570a405b831a781a99a32d875889a1428fd14', '29c723092833760b5798be581b9d7541b4c08eca56d994cdd490c667f1a36275', '8a2c37bf7e36269dd8f6f4ef3c41617aec9827a7584a1ce24d36330ac67daf81', '14bc18b4510959fb8bc9636ffdf54941df2d35455b9cb9b5d4e0ed65b0be9c99', '86c8fb996a3efc070a7a21b4a5fd68a3cea25ee238d9b49d06dd7eba79026e9f', 'e301bc0a00260ff030882fce35e20da68032ab0292a5799e1062d6c363a9dc72', 'c05797a50c8ad6afa69352a79da59f4a4c21f8c97c0c5066fc530a606bb777c3', 'a23f291bbb4705213ab7f7c5dd1c2d1cbcae1cf2fafb8904c48252b53f14a778', 'f7ece5de090445b6e9d67e84d50f5080d5367dde3d8867d0a0cb5210c9fb4000', '6ec4249787e6952696143d6e46ddea1d394f5e733e42e731c55d0c44b2e910dd', 'b5291a34aacfc156448faa33a0d6e3679d71ac7b2386e2096d12c610c68f0df5', '19679c538a6f375a418c47f987d18810db2799b96b0a8db25702b2e782acf372', '527f454199a3dfc7aa45e86f046afc245773818ab45565a979a10eb323e289dc', '23195ef015a2a08c4cc8c07f8508e324394294cdb4347ad2280a8641e5bb2983', 'd79875021e4fe494612ca9c10cdd6178a3007bc898b652565452d656497c9d40', '9d5c443dd4a368b4810ebf6c103f1ea06288eae0850884b0dc2786365bc41069', '3e25bd12ef1a23f77a8418efc3e2129f65a5321fb8cf1c3a2349b18186cda145', '46c9bb6d24a874d6119824a0676c7ff292a4e58813092ea993b27afad7fd27e8', 'c0993b2cfe35c5af651308bcdd4d94ef364ac70d3ae8bb66d4271cd9a1e8039e', '6653aafce754bdc5c5d5d2ad4f7ef05e9d7eb91e29f9b8ab9b7a427e63a95254', '4cb595abfd06843a47e823bd5aff7a0dea34d9d2a8ef455117ad9b4757b91dea', 'fb82dddcc3a634958f20d95dff47f6f7943c593d908765ecfadbc7509a4780be', 'f92fa19080f3ea4ccde1ad4085350fa6c6f218a6b38ce6afe76662453081bd28', 'c7c3c80e3b9748f93f46c9f0d0dd4a98e183a56ea22439f654911b9f3d4e0bd2', 'c9f05e91f854dd893ffafaa0eea8dcd1745d49d7a2226e68fa9e2720e7da6749', '0aac09a010fceda6e071eee4081e83d652aff96744916f732a16b9415225e4f7', '88d6294af55b97ccf47dc47c793b2b9eaf75ca5ccc934c73615a77fb3b9bdec2', '28940fee320a2ee80f582029a21167cc1b4a383e0fdfaf0c03a42bccc2100327', 'd95c6c511f9bc252e267f93795f46df8f4a0e5fa0b00cd14b286b346573f1d14', '32acd25cf97c778a0646480f896a72ceb93aafd20a14d72d6e5e2cbb1466a5c8', '86bb67215ced18e97d7ff1d072d7e7eceef1eb30401b6d96e3937508f7e752c9', '6e5bfb58faae4b41d0026905d37370fe6495083c1c4f90eb1cd3b68e78d70498', 'c7bdd6dc3f0bd4688ca8bd1f7a772e6ca65a42f3846ed0df3b879869b2d1f61e', '153d7ac58a40d9b865747bedb763fd2788087b32a837b5a369fb40319c866498', '7a427fdd95c55103681d73738d56c5c34e36b24a52614bcd4f08f910d78654c5', '967ef22132c91e2aaeed9c5bd894b0c4b7481c54c1dc30c427abacd83b77d7d3', 'd01cd44da6ebc24aca449c1588a61d4d1e8e6917dc0dfeb02f692bff5f9c3297', 'fcde8fe4315b320c4d05f0bb84f6bad20d0aa3e489afb03fec409eb15a4d8a20', '22322f72cbec061f23e045d4b9fd77a199bc18112a087cef360aa1b28d556f18', '9348a0e454c6eaa069a2888f4d4234449cc7a9bddb6ec72904d887a5578e1f0d', '7165c1aa304eb6dd606d568699b4bbcc3e097a525ae59ebb6f79c581e153a9f4', '1f39d6454ed23eca9203a8e082257e2fbaabfdbd98b9350856c849245675eaf0', '8722e1000f6429c47fa4b5f252e0fc11a4947d21260e6e98aca2d368c923c55c', '40a0689dc785bde315c7f31fae2b3898c34d5f59e5ffa6f157d74ccdc6736600', '2008b11634ccabac1ce8bf43a4f028fceeba23931846d37a0eee7f3e27252710', 'a5fa6d15d60fa762a18045826ca149bbacda3b30b9ed37eec4ca71e001a8b1aa', 'd9e8401f4fa35a369d23b021c43de4e9fa57c0861a64105b1011d1499ec740fd', 'e0acfd0fd28072e658abaea7d14e9ffae0e7cd97c9b59bec03aa9c32f352deea', '3ddde2bd4ce3f8ca64eb3d9930ced2c5da8c9e5635076f40a737f7a6c9db71e3', 'cfc04f8837e701a3354ce51c6cc348944e6eaadc05725e8d158287ad56fea146', '47680a2175cf040c0440c46601fed2d0a47d99c673ab257248a8706f64d11ac9', '94b8b5d77a4ad436dc20feef14f7b808f2445b36b426f7cc5a4de17a3b2ec858', '02e0340f606b637aa4c62cba75ce26661843923fd7248fa375f654e862f16cd4', '1aef4da701006b7a7dc107716a9b0ab4c7dad501fb8ef470a30a6f94bd49d5de', 'f0b5d78f138080b5a4e7c3f791972a529c7237ec657a19993635fc1dcad54c6a', '62a1a8ffee54e7563dd5bbd7a4f9cac7eec09b00ae71bb0689b2f579b62e30a7', 'fb502b9e6f14c87747cd15fb72a696664d92f7567682c562750fa07e7209b8ac', '0900bd5170ea73899052593f3c434daabc593033d9424758c38bd2b500e281c1', '38ae0f7292b5d25dd36937fbacd2f76664cc4e18f052bb0bb59b256ba9c04fa7', 'ed1dc7fd336e58bbfa340ef9a1ef3ed5fe134f09115a865b3efb46e2221fa4b8', 'c1180f8d95eaf405ab5f11d03279f9ccf064bc1222c36489a200e3aa1ff2910f', '4ac4146d58b36e7d6480db3cf0677dbb2f73a2bcec8a16f47510790e45e55e08', 'b4ef0a7b87f16a8b18f3963d9318abda910900fd87b15d3f1da2772433e0522b', '6b1c73ae7b1e60aef2d73c5de8f3ee06d220f836e0f8c5daa9255f8c2b4a2c9b', 'ac88efb147101037b5f69d2706b4a2310cfca51af4dad9aa7033cb9e985c9755', '379d4ddf44438eb16515cffb897e741e63f6b36ec0b7893251f089888e8bcd91', '05e0a06d3564a0423ca97bf0a78550cda331e1dccdccee2251bab688a98fbb48', '676cd7620a696c2b5db7dd847bc12412ff8fb0095ea1d85eeed8accdf853c19b', '63e47c43350da18555f96fe059a7bad9c12be72e83aa6083a87dd4964cf35099', '41f69dffd49e45b267bfd1846231ccd2bd47d954e3547c83f675fe779f7deab9', '38f2ae80afab0f9d01e42e2ad3f9f7f5e8c1c8cc736786703905e2f2ab8b0622']

#VIP_userIDs = ["6b1c73ae7b1e60aef2d73c5de8f3ee06d220f836e0f8c5daa9255f8c2b4a2c9b"]
VIP_userIDs = [int(userID,16) for userID in VIP_userIDs]

def get_userdata_from_db(db_path, userID):
	userID = int(userID,16)
	start_time = time()
	
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	cursor.execute(f"SELECT categoryType,startTime,endTime,views FROM sponsorTimes WHERE userID=\"{userID}\"")
	rows = cursor.fetchall()
	end_time = time()

	"""
	user_data = dict()
	user_data["submissions"] = dict()
	user_data["time saved"] = dict()
	user_data["views"] = dict()

	for category in categories:
		user_data["submissions"][category] = {"mute": 0,"skip": 0}
		user_data["time saved"][category] = 0
		user_data["views"][category] = {"mute": 0,"skip": 0}

	user_data["submissions"]["sponsor"]["full"] = 0
	user_data["submissions"]["selfpromo"]["full"] = 0
	user_data["submissions"]["poi_highlight"] = 0

	user_data["submissions"]["chapter"] = 0
	user_data["submissions"]["exclusive_access"] = 0

	# the above code regenerates this empty dict:
	"""

	user_data = {"submissions": {"filler": {"mute": 0, "skip": 0}, "intro": {"mute": 0, "skip": 0}, "outro": {"mute": 0, "skip": 0}, "sponsor": {"mute": 0, "skip": 0, "full": 0}, "selfpromo": {"mute": 0, "skip": 0, "full": 0}, "preview": {"mute": 0, "skip": 0}, "interaction": {"mute": 0, "skip": 0}, "nonmusic": {"mute": 0, "skip": 0}, "poi_highlight": 0, "chapter": 0, "exclusive_access": 0}, "time saved": {"filler": 0, "intro": 0, "outro": 0, "sponsor": 0, "selfpromo": 0, "preview": 0, "interaction": 0, "nonmusic": 0}, "views": {"filler": {"mute": 0, "skip": 0}, "intro": {"mute": 0, "skip": 0}, "outro": {"mute": 0, "skip": 0}, "sponsor": {"mute": 0, "skip": 0}, "selfpromo": {"mute": 0, "skip": 0}, "preview": {"mute": 0, "skip": 0}, "interaction": {"mute": 0, "skip": 0}, "nonmusic": {"mute": 0, "skip": 0}}}

	for row in rows:
		categoryType,startTime,endTime,views = row
		category, segment_type = categoryType

		category = expanded_categories[category]
		segment_type = expanded_types[segment_type]
		duration = float(endTime) - float(startTime)
		views = int(views)

		if category in ["poi_highlight", "chapter", "exclusive_access"]:
			user_data["submissions"][category] += 1
		else:
			user_data["submissions"][category][segment_type] += 1
			if segment_type != "full":
				user_data["views"][category][segment_type] += views
				user_data["time saved"][category] += duration

	print(f"Time taken: {round(end_time-start_time, 2)}")
	return user_data
    
mini_archive_location = "/mnt/WhiteBox/SponsorBlock/archive/sponsorTimes_sql"
userID = "6b1c73ae7b1e60aef2d73c5de8f3ee06d220f836e0f8c5daa9255f8c2b4a2c9b"

user_data = {"userID":userID}

for filename in os.listdir(mini_archive_location):
	filepath = os.path.join(mini_archive_location, filename)
	date = filename.split("_")[0]
	try:
		user_data[date] = get_userdata_from_db(filepath, userID)
	except Exception as ex:
		print(f"Exception for {filename} - {ex}")

with open("userdata.json", "w") as f:
	f.write(json.dumps(user_data))
	
result = requests.post("https://leaderboard.sbstats.uk/addUserData", headers={"Authorisation":"Bearer njQgB14IlKpAsw96IUOH6hJ1LKfJCqL996plKyvii11inPvFyheXzFgHQp060S4x"}, json=json.dumps(user_data))