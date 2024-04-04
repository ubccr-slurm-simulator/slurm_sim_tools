make_events_diagramm <- function(events1, events2) {
  events1$job_rec_id2 <- events1$job_rec_id-0.2
  events2$job_rec_id2 <- events2$job_rec_id+0.2

  df <- rbind(events1,events2) |>
    dplyr::mutate(id=paste(slurm_mode,dtstart,run_id)) |>
    dplyr::arrange(run_id,t)
  dfs <- dplyr::filter(df, metric %in% c("submit_job","launch_job","job_epilog_complete")) |>
    dplyr::select(id,job_rec_id,job_rec_id2,metric,t) |>
    dplyr::group_by(id,job_rec_id,metric) |>
    dplyr::summarise(job_rec_id2=last(job_rec_id2),t=last(t)) |>
    tidyr::spread(metric,t)


  marker <- list(size=10, line=list(width=2))
  p <- plotly::plot_ly(df) |>
      plotly::add_segments(
        data = dplyr::filter(df, metric=='backfill'), y=I(1000),yend=I(1021),
        x=~t,xend=~t,color=I("grey"),alpha=I(0.5), linetype=~id,
        name="backfiller start") |>
      plotly::add_segments(
        data = dplyr::filter(df, metric=='sched'), y=I(1000),yend=I(1021),
        x=~t,xend=~t,color=I("#AED6F1"),alpha=I(0.5), linetype=~id,
        name="sched start") |> #light blue
      plotly::add_segments(
        data = dplyr::filter(df, metric=='job_time_limits_testing'), y=I(1000),yend=I(1021),
        x=~t,xend=~t,color=I("#AEF1D6"),alpha=I(0.5), linetype=~id,
        name="timelim check") |> #light green
      plotly::add_segments(
        data = dfs, y=~job_rec_id2,yend=~job_rec_id2,
        x=~submit_job,xend=~launch_job,color=I("grey"),
        name="Wait Period") |>
      plotly::add_segments(
        data = dfs, y=~job_rec_id2,yend=~job_rec_id2,
        x=~launch_job,xend=~job_epilog_complete,color=I("red"),
        name="Run Period") |>
      plotly::add_markers(
        data = df |> dplyr::filter(metric=="submit_job"),
        y=~job_rec_id2, x=~t, color=I("grey"), symbol=I('o'),
        name="Submit Time",marker=marker) |>
      plotly::add_markers(
        data = df |> dplyr::filter(metric=="launch_job"),
        y=~job_rec_id2, x=~t, color=~value, colors=c("#0000FF","#00FF00"),
        symbol=I('cross'),marker=marker) |> #I('+')
      plotly::add_markers(
        data = df |> dplyr::filter(metric=="job_epilog_complete"),
        y=~job_rec_id2, x=~t, color=I("red"), symbol=I('x'),
        name="End Time",marker=marker) |>
      plotly::add_paths(
        data = df |> dplyr::filter(metric=="launch_job"),
        y=~job_rec_id2,x=~t, linetype=~id, legendgroup="Execution Order",
        color=I('black')) |>
      plotly::layout(
        yaxis = list(dtick = 1),
        xaxis = list(dtick = 10)
      )
  p
}