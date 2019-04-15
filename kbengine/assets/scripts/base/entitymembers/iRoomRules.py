# -*- coding: utf-8 -*-

import KBEngine
from KBEDebug import *
import utility
import const
import random

class iRoomRules(object):

	def __init__(self):
		# 房间的牌堆
		self.tiles = []

	def swapSeat(self, swap_list):
		random.shuffle(swap_list)
		for i in range(len(swap_list)):
			self.players_list[i] = self.origin_players_list[swap_list[i]]

		for i,p in enumerate(self.players_list):
			if p is not None:
				p.idx = i

	def setPrevailingWind(self):
		#圈风
		if self.player_num != 4:
			return
		minDearerNum = min(self.dealerNumList)
		self.prevailing_wind = const.WINDS[(self.prevailing_wind + 1 - const.WIND_EAST)%len(const.WINDS)] if minDearerNum >= 1 else self.prevailing_wind
		self.dealerNumList = [0] * self.player_num if minDearerNum >= 1 else self.dealerNumList
		self.dealerNumList[self.dealer_idx] += 1

	def setPlayerWind(self):
		if self.player_num != 4:
			return
		#位风
		for i,p in enumerate(self.players_list):
			if p is not None:
				p.wind = (self.player_num + i - self.dealer_idx)%self.player_num + const.WIND_EAST

	def initTiles(self):
		# 万 条 筒
		self.tiles = list(const.CHARACTER) * 4 + list(const.BAMBOO) * 4 + list(const.DOT) * 4
		# 东 西 南 北
		self.tiles += [const.WIND_EAST, const.WIND_SOUTH, const.WIND_WEST, const.WIND_NORTH] * 4
		# 中 发 白
		self.tiles += [const.DRAGON_RED, const.DRAGON_GREEN, const.DRAGON_WHITE] * 4
		# # 春 夏 秋 冬
		# self.tiles += [const.SEASON_SPRING, const.SEASON_SUMMER, const.SEASON_AUTUMN, const.SEASON_WINTER]
		# # 梅 兰 竹 菊
		# self.tiles += [const.FLOWER_PLUM, const.FLOWER_ORCHID, const.FLOWER_BAMBOO, const.FLOWER_CHRYSANTHEMUM]
		DEBUG_MSG("room:{},curround:{} init tiles:{}".format(self.roomID, self.current_round, self.tiles))
		self.shuffle_tiles()

	def shuffle_tiles(self):
		random.shuffle(self.tiles)
		DEBUG_MSG("room:{},curround:{} shuffle tiles:{}".format(self.roomID, self.current_round, self.tiles))

	def deal(self, prefabHandTiles, prefabTopList):
		""" 发牌 """
		if prefabHandTiles is not None:
			for i,p in enumerate(self.players_list):
				if p is not None and len(prefabHandTiles) >= 0:
					p.tiles = prefabHandTiles[i] if len(prefabHandTiles[i]) <= const.INIT_TILE_NUMBER else prefabHandTiles[i][0:const.INIT_TILE_NUMBER]
			topList = prefabTopList if prefabTopList is not None else []
			allTiles = []
			for i, p in enumerate(self.players_list):
				if p is not None:
					allTiles.extend(p.tiles)
			allTiles.extend(topList)

			tile2NumDict = utility.getTile2NumDict(allTiles)
			warning_tiles = [t for t, num in tile2NumDict.items() if num > 4]
			if len(warning_tiles) > 0:
				WARNING_MSG("room:{},curround:{} prefab {} is larger than 4.".format(self.roomID, self.current_round,
																					 warning_tiles))
			for t in allTiles:
				if t in self.tiles:
					self.tiles.remove(t)
			for i in range(const.INIT_TILE_NUMBER):
				num = 0
				for j in range(self.player_num):
					if len(self.players_list[j].tiles) >= const.INIT_TILE_NUMBER:
						continue
					self.players_list[j].tiles.append(self.tiles[num])
					num += 1
				self.tiles = self.tiles[num:]

			newTiles = topList
			newTiles.extend(self.tiles)
			self.tiles = newTiles
		else:
			for i in range(const.INIT_TILE_NUMBER):
				for j in range(self.player_num):
					self.players_list[j].tiles.append(self.tiles[j])
				self.tiles = self.tiles[self.player_num:]

		for i, p in enumerate(self.players_list):
			DEBUG_MSG("room:{},curround:{} idx:{} deal tiles:{}".format(self.roomID, self.current_round, i, p.tiles))

	def kongWreath(self):
		""" 杠花 """
		for i in range(self.player_num):
			for j in range(len(self.players_list[i].tiles)-1, -1, -1):
				tile = self.players_list[i].tiles[j]
				if tile in const.SEASON or tile in const.FLOWER:
					del self.players_list[i].tiles[j]
					self.players_list[i].wreaths.append(tile)
					DEBUG_MSG("room:{},curround:{} kong wreath, idx:{},tile:{}".format(self.roomID, self.current_round, i, tile))

	def addWreath(self):
		""" 补花 """
		for i in range(self.player_num):
			while len(self.players_list[i].tiles) < const.INIT_TILE_NUMBER:
				if len(self.tiles) <= 0:
					break
				tile = self.tiles[0]
				self.tiles = self.tiles[1:]
				if tile in const.SEASON or tile in const.FLOWER:
					self.players_list[i].wreaths.append(tile)
					DEBUG_MSG("room:{},curround:{} add wreath, tile is wreath,idx:{},tile:{}".format(self.roomID, self.current_round, i, tile))
				else:
					self.players_list[i].tiles.append(tile)
					DEBUG_MSG("room:{},curround:{} add wreath, tile is not wreath, idx:{},tile:{}".format(self.roomID, self.current_round, i, tile))

	def rollKingTile(self):
		""" 财神 """
		self.kingTiles = []
		if self.king_num > 0:
			for i in range(len(self.tiles)): 
				t = self.tiles[i]
				if t not in const.SEASON and t not in const.FLOWER: #第一张非花牌
					# 1-9为一圈 东南西北为一圈 中发白为一圈
					self.kingTiles.append(t)
					if self.king_num > 1:
						for tup in (const.CHARACTER, const.BAMBOO, const.DOT, const.WINDS, const.DRAGONS):
							if t in tup:
								index = tup.index(t)
								self.kingTiles.append(tup[(index + 1)%len(tup)])
								break
					del self.tiles[i]
					break

	def tidy(self):
		""" 整理 """
		for i in range(self.player_num):
			self.players_list[i].tidy(self.kingTiles)

	def throwTheDice(self, idxList):
		if self.player_num == 3:
			diceList = [[0, 0], [0, 0], [0, 0]]
		else:
			diceList = [[0, 0], [0, 0], [0, 0], [0, 0]]
		for idx in idxList:
			for i in range(0,2):
				diceNum = random.randint(1, 6)
				diceList[idx][i] = diceNum
		return diceList

	def getMaxDiceIdx(self, diceList):
		numList = []
		for i in range(len(diceList)):
			numList.append(diceList[i][0] + diceList[i][1])

		idx = 0
		num = 0
		for i in range(len(numList)):
			if numList[i] > num:
				idx = i
				num = numList[i]
		return idx, num

	def drawLuckyTile(self):
		luckyTileList = []
		for i in range(self.lucky_num):
			if len(self.tiles) > 0:
				luckyTileList.append(self.tiles[0])
				self.tiles = self.tiles[1:]
		return luckyTileList

	# def getKongRecord(self):
	# 	kong_record_list = []
	# 	for i in range(len(self.op_record)):
	# 		if self.op_record[i][0] == const.OP_CONCEALED_KONG or self.op_record[i][0] == const.OP_EXPOSED_KONG or self.op_record[i][0] == const.OP_CONTINUE_KONG:
	# 			kong_record_list.append(self.op_record[i])
	# 	return kong_record_list

	def getContinueKongFrom(self, op_r, tile):
		for record in reversed(op_r):
			if record[0] == const.OP_PONG and tile in record[1]:
				return record[2]
		return -1

	def getKongRecord(self):
		kong_record_list = []
		for i,p in enumerate(self.players_list):
			if p is not None:
				kong_record_list.extend(p.kong_record_list)
		return kong_record_list

	def cal_lucky_tile_score(self, lucky_tiles, winIdx):
		kong_record_list = self.getKongRecord() #(const.OP_EXPOSED_KONG, self.idx, self.owner.last_player_idx, [tile,])
		for t in lucky_tiles:
			#摸到第几个人
			idx = -99
			for i in range(len(const.LUCKY_TUPLE)):
				if t in const.LUCKY_TUPLE[i]:
					idx = i
					break
			sel_idx = (self.dealer_idx + idx) % self.player_num

			DEBUG_MSG("cal_lucky_tile_score sel_idx:{0}, luckyTile:{1}".format(sel_idx, t))
			if sel_idx < 0:
				continue
			#杠分
			kong_base_score = 1
			mul = 2 if self.game_mode == 1 else 1
			for record in kong_record_list:
				if record[0] == const.OP_CONCEALED_KONG: #暗杠
					if sel_idx == self.dealer_idx: #摸到自己
						if record[1] == sel_idx: #是自己杠 6 -2 -2 -2
							# 相当于自己再杠一遍
							for i,p in enumerate(self.players_list):
								if p is not None and i != sel_idx:
									p.add_treasure_kong_score(-mul * kong_base_score)
							self.players_list[self.dealer_idx].add_treasure_kong_score(mul* kong_base_score * (self.player_num-1))
						else: #不是自己杠 -2 4 -1 -1
							#自己扣2分 杠的人再得2分
							self.players_list[self.dealer_idx].add_treasure_kong_score(-mul* kong_base_score)
							self.players_list[record[1]].add_treasure_kong_score(mul* kong_base_score)
					else: #摸到别人
						# 是自己杠 不加不减
						# 是别人杠
						if record[1] != self.dealer_idx: 
							#摸到得分的人 除得分的人外全部扣一遍 自己加得分 -2 4 -1 -1
							if record[1] == sel_idx:
								for i,p in enumerate(self.players_list):
									if p is not None and i != sel_idx:
										if i == self.dealer_idx:
											p.add_treasure_kong_score(-mul* kong_base_score)
										else:
											p.add_treasure_kong_score(-kong_base_score)
								self.players_list[self.dealer_idx].add_treasure_kong_score(kong_base_score * (self.player_num -2 + mul))
							else:
								#摸到 扣分的人，自己扣分，杠的人得分 -2 -1 -1 4
								self.players_list[record[1]].add_treasure_kong_score(kong_base_score)
								self.players_list[self.dealer_idx].add_treasure_kong_score(-kong_base_score)
				elif record[0] == const.OP_CONTINUE_KONG:
					fromIdx = self.getContinueKongFrom(self.players_list[record[1]].op_r, record[3][0])
					if sel_idx == record[1]: # 接杠
						score = mul * kong_base_score if (record[1] == self.dealer_idx or fromIdx == self.dealer_idx) else kong_base_score
						self.players_list[fromIdx].add_treasure_kong_score(-score)
						self.players_list[self.dealer_idx].add_treasure_kong_score(score)
					elif sel_idx == fromIdx: # 被接杠
						score = mul * kong_base_score if (record[1] == self.dealer_idx or fromIdx == self.dealer_idx) else kong_base_score
						self.players_list[record[1]].add_treasure_kong_score(score)
						self.players_list[self.dealer_idx].add_treasure_kong_score(-score)
				elif record[1] == sel_idx: #明杠
					score = mul * kong_base_score if (record[1] == self.dealer_idx or record[2] == self.dealer_idx) else kong_base_score
					DEBUG_MSG("lucky exposed kong,idx:{0}, fromIdx:{1} score:{2}".format(record[1], record[2],score))
					self.players_list[record[2]].add_treasure_kong_score(-score)
					self.players_list[self.dealer_idx].add_treasure_kong_score(score)
				elif record[2] == sel_idx: #被明杠
					score = mul * kong_base_score if (record[1] == self.dealer_idx or record[2] == self.dealer_idx) else kong_base_score
					DEBUG_MSG("kucky be exposed kong,idx:{0}, fromIdx:{1} score:{2}".format(record[1], record[2],score))
					self.players_list[record[1]].add_treasure_kong_score(score)
					self.players_list[self.dealer_idx].add_treasure_kong_score(-score)
			if winIdx >= 0: # 非流局
				sel_score = self.players_list[sel_idx].score
				if sel_idx == winIdx: # 摸胡牌的人
					for i,p in enumerate(self.players_list):
						if i != sel_idx and p is not None:
							p.add_treasure_score(p.score)
					self.players_list[self.dealer_idx].add_treasure_score(sel_score)
				else:
					self.players_list[self.dealer_idx].add_treasure_score(sel_score)
					self.players_list[winIdx].add_treasure_score(-sel_score)

	def swapTileToTop(self, tile):
		if tile in self.tiles:
			tileIdx = self.tiles.index(tile)
			self.tiles[0], self.tiles[tileIdx] = self.tiles[tileIdx], self.tiles[0]

	def winCount(self):
		pass

	def canTenPai(self, handTiles):
		length = len(handTiles)
		if length % 3 != 1:
			return False

		result = []
		tryTuple = (const.CHARACTER, const.BAMBOO, const.DOT, const.WINDS, const.DRAGONS)
		for tup in tryTuple:
			for t in tup:
				tmp = list(handTiles)
				tmp.append(t)
				sorted(tmp)
				if utility.isWinTile(tmp, self.kingTiles):
					result.append(t)
		return result != []


	def can_cut_after_kong(self):
		return True

	def can_discard(self, tiles, t):
		if t in tiles:
			return True
		return False

	def can_chow(self, tiles, t):
		return	False
		# if t >= 30:
		# 	return False
		# neighborTileNumList = [0, 0, 1, 0, 0]
		# for i in range(len(tiles)):
		# 	if (tiles[i] - t >= -2 and tiles[i] - t <= 2):
		# 		neighborTileNumList[tiles[i] - t + 2] += 1
		# for i in range(0,3):
		# 	tileNum = 0
		# 	for j in range(i,i+3):
		# 		if neighborTileNumList[j] > 0:
		# 			tileNum += 1
		# 		else:
		# 			break
		# 	if tileNum >= 3:
		# 		return True
		# return False

	def can_chow_list(self, tiles, tile_list):
		return False
		# """ 能吃 """
		# if tile_list[0] >= 30:
		# 	return False
		# if sum([1 for i in tiles if i == tile_list[1]]) >= 1 and sum([1 for i in tiles if i == tile_list[2]]) >= 1:
		# 	sortLis = sorted(tile_list)
		# 	if (sortLis[2] + sortLis[0])/2 == sortLis[1] and sortLis[2] - sortLis[0] == 2:
		# 		return True
		# return False

	def can_pong(self, tiles, t):
		""" 能碰 """
		if t in self.kingTiles:
			return False
		return sum([1 for i in tiles if i == t]) >= 2

	def can_exposed_kong(self, tiles, t):
		""" 能明杠 """
		if t in self.kingTiles:
			return False
		return tiles.count(t) == 3

	def can_continue_kong(self, player, t):
		""" 能够风险杠 """
		if t in self.kingTiles:
			return False
		for op in player.op_r:
			if op[0] == const.OP_PONG and op[1][0] == t:
				return True
		return False

	def can_concealed_kong(self, tiles, t):
		""" 能暗杠 """
		if t in self.kingTiles:
			return False
		return tiles.count(t) == 4

	def can_kong_wreath(self, tiles, t):
		if t in tiles and (t in const.SEASON or t in const.FLOWER):
			return True
		return False

	def can_wreath_win(self, wreaths):
		if len(wreaths) == len(const.SEASON) + len(const.FLOWER):
			return True
		return False

	def can_change_discard_state(self, tiles, i, state):
		if state == const.DISCARD_FREE:
			return False
		elif state == const.DISCARD_FORCE:
			return self.canTenPai(tiles)

	def getNotifyOpList(self, idx, aid, tile):
		# notifyOpList 和 self.wait_op_info_list 必须同时操作
		# 数据结构：问询玩家，操作玩家，牌，操作类型，得分，结果，状态
		notifyOpList = [[] for i in range(self.player_num)]
		self.wait_op_info_list = []
		#胡
		if aid == const.OP_KONG_WREATH and self.can_wreath_win(self.players_list[idx].wreaths): # 8花胡
			opDict = {"idx":idx, "from":idx, "tileList":[tile,], "aid":const.OP_WREATH_WIN, "score":0, "result":[], "state":const.OP_STATE_WAIT}
			notifyOpList[idx].append(opDict)
			self.wait_op_info_list.append(opDict)
		elif aid == const.OP_EXPOSED_KONG: #直杠 抢杠胡
			wait_for_win_list = self.getExposedKongWinList(idx, tile)
			self.wait_op_info_list.extend(wait_for_win_list)
			for i in range(len(wait_for_win_list)):
				dic = wait_for_win_list[i]
				notifyOpList[dic["idx"]].append(dic)
		elif aid == const.OP_CONTINUE_KONG: #碰后接杠 抢杠胡
			wait_for_win_list = self.getKongWinList(idx, tile)
			self.wait_op_info_list.extend(wait_for_win_list)
			for i in range(len(wait_for_win_list)):
				dic = wait_for_win_list[i]
				notifyOpList[dic["idx"]].append(dic)
		elif aid == const.OP_DISCARD:
			#胡(放炮胡)
			wait_for_win_list = self.getGiveWinList(idx, tile)
			self.wait_op_info_list.extend(wait_for_win_list)
			for i in range(len(wait_for_win_list)):
				dic = wait_for_win_list[i]
				notifyOpList[dic["idx"]].append(dic)
			#杠 碰
			for i, p in enumerate(self.players_list):
				if p and i != idx:
					if self.can_exposed_kong(p.tiles, tile):
						opDict = {"idx":i, "from":idx, "tileList":[tile,], "aid":const.OP_EXPOSED_KONG, "score":0, "result":[], "state":const.OP_STATE_WAIT}
						self.wait_op_info_list.append(opDict)
						notifyOpList[i].append(opDict)
					if self.can_pong(p.tiles, tile):
						opDict = {"idx":i, "from":idx, "tileList":[tile,], "aid":const.OP_PONG, "score":0, "result":[], "state":const.OP_STATE_WAIT}
						self.wait_op_info_list.append(opDict)
						notifyOpList[i].append(opDict)
			#吃
			nextIdx = self.nextIdx
			if self.can_chow(self.players_list[nextIdx].tiles, tile):
				opDict = {"idx":nextIdx, "from":idx, "tileList":[tile,], "aid":const.OP_CHOW, "score":0, "result":[], "state":const.OP_STATE_WAIT}
				self.wait_op_info_list.append(opDict)
				notifyOpList[nextIdx].append(opDict)
		return notifyOpList

	def getExposedKongWinList(self, idx, tile):
		wait_for_win_list = []
		for i,p in enumerate(self.players_list):
			if p is not None and i != idx:
				# 抢直杠 卡张 必须卖宝
				if p.discard_tiles and tile == p.discard_tiles[-1] and utility.getCanWinTiles(p.tiles) == [tile]:
					DEBUG_MSG("getExposedKongWinList {}".format(i))
					tryTiles = list(p.tiles)
					tryTiles.append(tile)
					tryTiles = sorted(tryTiles)
					_, score, result = self.can_win(tryTiles, tile, const.OP_KONG_WIN, i)
					wait_for_win_list.append({"idx":i, "from":idx, "tileList":[tile,], "aid":const.OP_KONG_WIN, "score":score, "result":result, "state":const.OP_STATE_WAIT})
				else: # 平胡 可以 抢直杠
					tryTiles = list(p.tiles)
					tryTiles.append(tile)
					tryTiles = sorted(tryTiles)
					isWin, score, result = self.can_win(tryTiles, tile, const.OP_KONG_WIN, i)
					if isWin and score == 1:
						wait_for_win_list.append({"idx": i, "from": idx, "tileList": [tile, ], "aid": const.OP_KONG_WIN, "score": score,"result": result, "state": const.OP_STATE_WAIT})
		return wait_for_win_list

	# 抢杠胡 玩家列表
	def getKongWinList(self, idx, tile):
		wait_for_win_list = []
		for i in range(self.player_num - 1):
			ask_idx = (idx+i+1)%self.player_num
			p = self.players_list[ask_idx]
			tryTiles = list(p.tiles)
			tryTiles.append(tile)
			tryTiles = sorted(tryTiles)
			DEBUG_MSG("room:{},curround:{} getKongWinList {}".format(self.roomID, self.current_round, ask_idx))
			is_win, score, result = self.can_win(tryTiles, tile, const.OP_KONG_WIN, ask_idx)
			if is_win:
				wait_for_win_list.append({"idx":ask_idx, "from":idx, "tileList":[tile,], "aid":const.OP_KONG_WIN, "score":score, "result":result, "state":const.OP_STATE_WAIT})
		return wait_for_win_list

	# 放炮胡 玩家列表
	def getGiveWinList(self, idx, tile):
		wait_for_win_list = []
		for i in range(self.player_num - 1):
			ask_idx = (idx+i+1)%self.player_num
			p = self.players_list[ask_idx]
			tryTiles = list(p.tiles)
			tryTiles.append(tile)
			tryTiles = sorted(tryTiles)
			DEBUG_MSG("getGiveWinList {0}".format(ask_idx))
			is_win, score, result = self.can_win(tryTiles, tile, const.OP_GIVE_WIN, ask_idx)
			if is_win:
				wait_for_win_list.append({"idx":ask_idx, "from":idx, "tileList":[tile,], "aid":const.OP_GIVE_WIN, "score":score, "result":result, "state":const.OP_STATE_WAIT})
		return wait_for_win_list

	def classify_tiles(self, tiles):
		chars = []
		bambs = []
		dots  = []
		dragon_red = 0
		for t in tiles:
			if t in const.CHARACTER:
				chars.append(t)
			elif t in const.BAMBOO:
				bambs.append(t)
			elif t in const.DOT:
				dots.append(t)
			elif t == const.DRAGON_RED:
				dragon_red += 1
			else:
				DEBUG_MSG("iRoomRules classify tiles failed, no this tile %s"%t)
		return chars, bambs, dots, dragon_red

	def can_win(self, handTiles, finalTile, win_op, idx):
		# 平胡 卡张 碰碰胡 全求人 7对 豪7 双豪7 三豪7 清一色 字一色 乱风 杠开
		result = [0] * 12  #胡牌类型
		quantity = 0
		if len(handTiles) % 3 != 2:
			return False, quantity, result
		
		p = self.players_list[idx]
		handCopyTiles = list(handTiles)
		handCopyTiles = sorted(handCopyTiles)
		classifyList = utility.classifyTiles(handCopyTiles, self.kingTiles)  
		kingTilesNum = len(classifyList[0])  #百搭的数量
		handTilesButKing = []  #除百搭外的手牌
		for i in range(1, len(classifyList)):
			handTilesButKing.extend(classifyList[i])
		upTiles = p.upTiles
		# 清一色 字一色 
		colorType = utility.getTileColorType(handTilesButKing, upTiles)
		# 7对
		is7Double, isBrightTiles, isDarkTiles = utility.get7DoubleWin(handCopyTiles, handTilesButKing, kingTilesNum, finalTile)

		# 获得所有能胡的牌的列表
		tmpTiles = list(handTiles)
		tmpTiles.remove(finalTile)
		canWinList = utility.getCanWinTiles(tmpTiles)
		
		isCanWin = False
		if is7Double:
			quantity += 4
			tile2NumDict = utility.getTile2NumDict(handTilesButKing)
			if colorType == const.SAME_SUIT:
				quantity += 4
				result[8] = 1
			elif colorType == const.SAME_HONOR:
				quantity += 4
				result[9] = 1
			mul = 0
			for t in tile2NumDict:
				if tile2NumDict[t] == 4:
					mul += 1
			quantity *= 2 ** mul
			result[4 + mul] = 1
			return True, quantity, result
		elif finalTile in canWinList:
			isPongPongWin = utility.checkIsPongPongWin(handTilesButKing, upTiles, kingTilesNum)
			isKongWin, kongWinType = utility.checkIsKongDrawWin(p.op_r)
			
			if isPongPongWin:
				# 碰碰胡
				quantity += 3
				result[2] = 1
				# 全求人
				if len(handCopyTiles) == 2: 
					quantity += 2
					result[3] = 1
				#清一色/字一色
				if colorType == const.SAME_SUIT:
					quantity += 4
					result[8] = 1
				elif colorType == const.SAME_HONOR:
					quantity += 4
					result[9] = 1
				# 杠开
				if win_op == const.OP_DRAW_WIN and isKongWin:
					quantity *= 2
					result[11] = 1
				isCanWin = True
			elif len(canWinList) == 1:
				# 卡张
				quantity += 2
				result[1] = 1
				#清一色 --不可能是字一色，字一色必须是碰碰胡
				if colorType == const.SAME_SUIT:
					quantity += 4
					result[8] = 1
				# 杠开
				if win_op == const.OP_DRAW_WIN and isKongWin:
					quantity *= 2
					result[11] = 1
				isCanWin = True
			else:
				#平胡 --不可能是字一色，字一色必须是碰碰胡
				quantity += 1
				result[0] = 1
				#清一色/字一色
				if colorType == const.SAME_SUIT:
					# 清一色
					quantity += 4
					result[8] = 1
					# 杠开
					if win_op == const.OP_DRAW_WIN and isKongWin:
						quantity *= 2
						result[11] = 1
					isCanWin = True
				elif win_op == const.OP_DRAW_WIN: # 平胡 非 清一色/字一色只能自摸
					# 杠开
					if win_op == const.OP_DRAW_WIN and isKongWin:
						quantity *= 2
						result[11] = 1
					isCanWin = True
				elif win_op == const.OP_KONG_WIN:
					isCanWin = True
		elif colorType == const.SAME_HONOR:
			quantity += 5
			result[10] = 1
			isCanWin = True
		return isCanWin, quantity, result


	def cal_score(self, idx, fromIdx, aid, score):
		if aid == const.OP_EXPOSED_KONG:
			if self.game_mode == 1 and (self.dealer_idx == idx or self.dealer_idx == fromIdx): #庄家翻倍模式
				self.players_list[fromIdx].add_kong_score(-2 * score)
				self.players_list[idx].add_kong_score(2 * score)
			else:
				self.players_list[fromIdx].add_kong_score(-score)
				self.players_list[idx].add_kong_score(score)
		elif aid == const.OP_CONTINUE_KONG:
			if self.game_mode == 1 and (self.dealer_idx == idx or self.dealer_idx == fromIdx): #庄家翻倍模式
				self.players_list[fromIdx].add_kong_score(-2 * score)
				self.players_list[idx].add_kong_score(2 * score)
			else:
				self.players_list[fromIdx].add_kong_score(-score)
				self.players_list[idx].add_kong_score(score)
		elif aid == const.OP_CONCEALED_KONG:
			if self.game_mode == 1:
				if self.dealer_idx == idx:
					for i, p in enumerate(self.players_list):
						if p is not None:
							if i == idx:
								p.add_kong_score(score * 2 * (self.player_num-1))
							else:
								p.add_kong_score(-score * 2)
				else:
					for i, p in enumerate(self.players_list):
						if p is not None:
							if i == idx:
								p.add_kong_score(score * self.player_num)
							elif i == self.dealer_idx:
								p.add_kong_score(-score * 2)
							else:
								p.add_kong_score(-score)
			else:
				for i, p in enumerate(self.players_list):
					if p is not None:
						if i == idx:
							p.add_kong_score(score * (self.player_num-1))
						else:
							p.add_kong_score(-score)
		elif aid == const.OP_DRAW_WIN:
			if self.game_mode == 1:
				if self.dealer_idx == idx:
					realLose = 0
					for i, p in enumerate(self.players_list):
						if p is not None and i != idx:
							realLose += p.add_score(-score * 2)
					self.players_list[idx].add_score(-realLose)
				else:
					realLose = 0
					for i, p in enumerate(self.players_list):
						if p is not None and i != idx:
							if i == self.dealer_idx:
								realLose += p.add_score(-score * 2)
							else:
								realLose += p.add_score(-score)
					self.players_list[idx].add_score(-realLose)
			else:
				realLose = 0
				for i, p in enumerate(self.players_list):
					if p is not None and i != idx:
						realLose += p.add_score(-score)
				self.players_list[idx].add_score(-realLose)
		elif aid == const.OP_KONG_WIN:
			realLose = 0
			if self.game_mode == 1 and (idx == self.dealer_idx or fromIdx == self.dealer_idx):
				realLose += self.players_list[fromIdx].add_score(-score * (self.player_num-1) * 2)
				self.players_list[idx].add_score(-realLose)
			else:
				realLose += self.players_list[fromIdx].add_score(-score * (self.player_num-1))
				self.players_list[idx].add_score(-realLose)
			#返还杠分
			kong_info = self.players_list[fromIdx].kong_record_list[-1]
			if kong_info[0] == const.OP_CONTINUE_KONG:
				continue_kong_from = self.getContinueKongFrom(self.players_list[fromIdx].op_r, kong_info[3][0])
				del self.players_list[fromIdx].kong_record_list[-1]
				self.cal_score(continue_kong_from, kong_info[1], kong_info[0], 1)
			else:
				del self.players_list[fromIdx].kong_record_list[-1]
				self.cal_score(kong_info[2], kong_info[1], kong_info[0], 1)
		elif aid == const.OP_GIVE_WIN:
			realLose = 0
			if self.game_mode == 1 and (idx == self.dealer_idx or fromIdx == self.dealer_idx):
				realLose += self.players_list[fromIdx].add_score(-score * 2)
				self.players_list[idx].add_score(-realLose)
			else:
				realLose += self.players_list[fromIdx].add_score(-score)
				self.players_list[idx].add_score(-realLose)
		elif aid == const.OP_WREATH_WIN:
			pass