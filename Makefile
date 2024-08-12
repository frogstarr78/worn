.PHONY: test coverage mock_data
all:
	echo all

test:
	bin/python3 -m unittest -v test/test_nocolors.py test/test_args.py test/test_db.py test/test_lib.py test/test_project.py test/test_faux_project.py test/test_log_project.py test/test_report.py

coverage:
	-bin/coverage run --source=lib --omit=lib/python3.11/** --module unittest -v test/test_nocolors.py test/test_args.py test/test_db.py test/test_lib.py test/test_project.py test/test_faux_project.py test/test_log_project.py test/test_report.py
	bin/coverage report --show-missing

define query =
endef

mock_data:
	redis-cli -n 2 dbsave
	redis-cli -n 2 FLUSHDB
	redis-cli -n 2 HSET projects 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 "Worn" worn 244019c2-6d8f-4b09-96c1-b60a91ecb3a5
	redis-cli -n 2 HSET projects 24dfbaed-6de1-4541-a3da-67bceffb3d82 "Order 3912" "order 3912" 24dfbaed-6de1-4541-a3da-67bceffb3d82
	redis-cli -n 2 HSET projects 2c68c577-17f6-4740-aae6-d02c9357c58e "Order 3934 Skink" "order 3934 skink" 2c68c577-17f6-4740-aae6-d02c9357c58e
	redis-cli -n 2 HSET projects 3a34a692-c801-4820-902c-e09db076d917 "CAUMDD" caumdd 3a34a692-c801-4820-902c-e09db076d917
	redis-cli -n 2 HSET projects 42c40a16-6960-440a-a03b-959af10cf151 "Walk-through" walk-through 42c40a16-6960-440a-a03b-959af10cf151
	redis-cli -n 2 HSET projects 442b87f8-b77d-4ab2-9365-dd3927d44566 "comms" comms 442b87f8-b77d-4ab2-9365-dd3927d44566
	redis-cli -n 2 HSET projects 55d56128-24aa-4b76-b162-e2f4aeeed1b5 "Order 3947" "order 3947" 55d56128-24aa-4b76-b162-e2f4aeeed1b5
	redis-cli -n 2 HSET projects 6315e7a9-c6c6-42e2-b20b-74981ce957d3 "Break/Restroom" "break/restroom" 6315e7a9-c6c6-42e2-b20b-74981ce957d3
	redis-cli -n 2 HSET projects be94900e-a4ed-4d94-bd96-9865b87a998e "Order 3911" "order 3911" be94900e-a4ed-4d94-bd96-9865b87a998e
	redis-cli -n 2 HSET projects cb03691f-61f8-49eb-85bb-e18f817267a7 "Ticket #1571471 fierce-saffron-gorilla upgrade" "ticket #1571471 fierce-saffron-gorilla upgrade" cb03691f-61f8-49eb-85bb-e18f817267a7
	redis-cli -n 2 HSET projects d20e7765-f771-4a77-a008-718f54439639 "Managerial Stuff" "managerial stuff" d20e7765-f771-4a77-a008-718f54439639
	redis-cli -n 2 HSET versions logs-5978e7f4-a433-4e53-88db-039f784948c9 "Populating alternate data"
	redis-cli -n 2 XADD logs-5978e7f4-a433-4e53-88db-039f784948c9 1708900766-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state started
	redis-cli -n 2 XADD logs-5978e7f4-a433-4e53-88db-039f784948c9 1708900773-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state stopped
	redis-cli -n 2 XADD logs-5978e7f4-a433-4e53-88db-039f784948c9 1708969116-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state started
	redis-cli -n 2 XADD logs-5978e7f4-a433-4e53-88db-039f784948c9 1709140092-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state stopped
	redis-cli -n 2 XADD logs 1708900766-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state started
	redis-cli -n 2 XADD logs 1708900773-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state stopped
	redis-cli -n 2 XADD logs 1708969114-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state started
	redis-cli -n 2 XADD logs 1709140090-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state stopped
	redis-cli -n 2 XADD logs 1709140090-1 project 442b87f8-b77d-4ab2-9365-dd3927d44566 state started
	redis-cli -n 2 XADD logs 1709142240-0 project 442b87f8-b77d-4ab2-9365-dd3927d44566 state stopped
	redis-cli -n 2 XADD logs 1709142240-1 project 42c40a16-6960-440a-a03b-959af10cf151 state started
	redis-cli -n 2 XADD logs 1709142900-0 project 42c40a16-6960-440a-a03b-959af10cf151 state stopped
	redis-cli -n 2 XADD logs 1709160561-0 project 442b87f8-b77d-4ab2-9365-dd3927d44566 state started
	redis-cli -n 2 XADD logs 1709162518-0 project 442b87f8-b77d-4ab2-9365-dd3927d44566 state stopped
	redis-cli -n 2 XADD logs 1709162518-1 project 24dfbaed-6de1-4541-a3da-67bceffb3d82 state started
	redis-cli -n 2 XADD logs 1709163346-0 project 24dfbaed-6de1-4541-a3da-67bceffb3d82 state stopped
	redis-cli -n 2 XADD logs 1709163346-1 project be94900e-a4ed-4d94-bd96-9865b87a998e state started
	redis-cli -n 2 XADD logs 1709163746-0 project be94900e-a4ed-4d94-bd96-9865b87a998e state stopped
	redis-cli -n 2 XADD logs 1710800105-0 project 2c68c577-17f6-4740-aae6-d02c9357c58e state started
	redis-cli -n 2 XADD logs 1710800383-0 project 2c68c577-17f6-4740-aae6-d02c9357c58e state stopped
	redis-cli -n 2 XADD logs 1710800383-1 project 2c68c577-17f6-4740-aae6-d02c9357c58e state started
	redis-cli -n 2 XADD logs 1710801150-0 project 2c68c577-17f6-4740-aae6-d02c9357c58e state stopped
	redis-cli -n 2 XADD logs 1710801150-1 project 2c68c577-17f6-4740-aae6-d02c9357c58e state started
	redis-cli -n 2 XADD logs 1710801905-0 project 2c68c577-17f6-4740-aae6-d02c9357c58e state stopped
	redis-cli -n 2 XADD logs 1710806812-0 project 3a34a692-c801-4820-902c-e09db076d917 state started
	redis-cli -n 2 XADD logs 1710806873-0 project 3a34a692-c801-4820-902c-e09db076d917 state stopped
	redis-cli -n 2 XADD logs 1710807467-0 project 6315e7a9-c6c6-42e2-b20b-74981ce957d3 state started
	redis-cli -n 2 XADD logs 1710808205-0 project 6315e7a9-c6c6-42e2-b20b-74981ce957d3 state stopped
	redis-cli -n 2 XADD logs 1711130847-1 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711130860-0 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1711130860-1 project d20e7765-f771-4a77-a008-718f54439639 state started
	redis-cli -n 2 XADD logs 1711131301-0 project d20e7765-f771-4a77-a008-718f54439639 state stopped
	redis-cli -n 2 XADD logs 1711131301-1 project 6315e7a9-c6c6-42e2-b20b-74981ce957d3 state started
	redis-cli -n 2 XADD logs 1711131432-0 project 6315e7a9-c6c6-42e2-b20b-74981ce957d3 state stopped
	redis-cli -n 2 XADD logs 1711131432-1 project 442b87f8-b77d-4ab2-9365-dd3927d44566 state started
	redis-cli -n 2 XADD logs 1711131818-0 project 442b87f8-b77d-4ab2-9365-dd3927d44566 state stopped
	redis-cli -n 2 XADD logs 1711131818-1 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711132201-0 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1711133101-1 project d20e7765-f771-4a77-a008-718f54439639 state started
	redis-cli -n 2 XADD logs 1711134001-0 project d20e7765-f771-4a77-a008-718f54439639 state stopped
	redis-cli -n 2 XADD logs 1711134001-1 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711134001-2 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1711134001-3 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711135801-0 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1711135801-1 project 6315e7a9-c6c6-42e2-b20b-74981ce957d3 state started
	redis-cli -n 2 XADD logs 1711136211-0 project 6315e7a9-c6c6-42e2-b20b-74981ce957d3 state stopped
	redis-cli -n 2 XADD logs 1711136211-1 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711136420-0 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1711136420-1 project cb03691f-61f8-49eb-85bb-e18f817267a7 state started
	redis-cli -n 2 XADD logs 1711136701-0 project cb03691f-61f8-49eb-85bb-e18f817267a7 state stopped
	redis-cli -n 2 XADD logs 1711136701-1 project cb03691f-61f8-49eb-85bb-e18f817267a7 state started
	redis-cli -n 2 XADD logs 1711143218-0 project cb03691f-61f8-49eb-85bb-e18f817267a7 state stopped
	redis-cli -n 2 XADD logs 1711143218-1 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711143520-0 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1711143520-1 project cb03691f-61f8-49eb-85bb-e18f817267a7 state started
	redis-cli -n 2 XADD logs 1711143901-0 project cb03691f-61f8-49eb-85bb-e18f817267a7 state stopped
	redis-cli -n 2 XADD logs 1711152002-1 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711152901-0 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1711152901-1 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711153801-0 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1711153801-1 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state started
	redis-cli -n 2 XADD logs 1711154701-0 project 55d56128-24aa-4b76-b162-e2f4aeeed1b5 state stopped
	redis-cli -n 2 XADD logs 1716658568-0 project 244019c2-6d8f-4b09-96c1-b60a91ecb3a5 state started
	redis-cli -n 2 dbsave
