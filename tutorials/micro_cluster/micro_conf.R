micro_nodes <- list(
    list(
        Name="Nodes_N",
        Nodes=python.call("expand_hostlist","n[1-4]"),
        Feature=c('IB','CPU-N'),
        Procs=12,
        RealMemory=48000,
        Gres=NA
    ),
    list(
        Name="Nodes_M",
        Nodes=python.call("expand_hostlist","m[1-4]"),
        Feature=c('IB','CPU-G'),
        Procs=12,
        RealMemory=48000,
        Gres=NA
    ),
    list(
        Name="Nodes_G",
        Nodes=python.call("expand_hostlist","g1"),
        Feature=c('IB','CPU-G'),
        Procs=12,
        RealMemory=48000,
        Gres='gpu:2'
    ),
    list(
        Name="Nodes_B",
        Nodes=python.call("expand_hostlist", "b1"),
        Feature=c('IB','CPU-G','BigMem'),
        Procs=12,
        RealMemory=512000,
        Gres=NA
    )
)
sapply(micro_nodes,function(n){n$Name})
names(micro_nodes) <- unique(sapply(micro_nodes,function(n){n$Name}))